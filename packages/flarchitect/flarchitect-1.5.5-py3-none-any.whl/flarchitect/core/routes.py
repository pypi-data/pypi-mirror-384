from __future__ import annotations

import base64
import binascii
import os
import secrets
import time
from collections.abc import Callable
from types import FunctionType
from typing import TYPE_CHECKING, Any

from flask import Blueprint, abort, g, request
from sqlalchemy import inspect as sa_inspect
from marshmallow import Schema
from sqlalchemy.orm import DeclarativeBase, Session
from werkzeug.exceptions import default_exceptions

from flarchitect.authentication.token_store import rotate_refresh_token
from flarchitect.authentication.user import set_current_user
from flarchitect.authentication.user import get_current_user
from flarchitect.core.utils import get_primary_key_info, get_url_pk
from flarchitect.database.operations import CrudService
from flarchitect.database.utils import get_models_relationships, get_primary_keys
from flarchitect.exceptions import CustomHTTPException, handle_http_exception
from flarchitect.logging import logger
from flarchitect.plugins import PluginManager
from flarchitect.schemas.auth import LoginSchema, RefreshSchema, TokenSchema
from flarchitect.schemas.utils import get_input_output_from_model_or_make
from flarchitect.specs.utils import (
    endpoint_namer,
    generate_additional_query_params,
    generate_delete_query_params,
    generate_get_query_params,
    get_param_schema,
    get_tag_group,
)
from flarchitect.utils.config_helpers import get_config_or_model_meta
from flarchitect.utils.core_utils import convert_case
from flarchitect.utils.general import AttributeInitialiserMixin
from flarchitect.utils.response_helpers import create_response
from flarchitect.utils.session import get_session
from flarchitect.core.discovery import build_schema_discovery_payload
from flarchitect.core.docbundle import build_docs_bundle

if TYPE_CHECKING:
    from flarchitect import Architect
    from flarchitect.authentication import jwt as _JwtModule


def _import_jwt_module():
    """Import the JWT helpers lazily to avoid circular dependencies."""

    from flarchitect.authentication import jwt

    return jwt


def _generate_access_token(*args: Any, **kwargs: Any):
    return _import_jwt_module().generate_access_token(*args, **kwargs)


def _generate_refresh_token(*args: Any, **kwargs: Any):
    return _import_jwt_module().generate_refresh_token(*args, **kwargs)


def _get_pk_and_lookups(*args: Any, **kwargs: Any):
    return _import_jwt_module().get_pk_and_lookups(*args, **kwargs)


def _refresh_access_token(*args: Any, **kwargs: Any):
    return _import_jwt_module().refresh_access_token(*args, **kwargs)


def _global_pre_process(service: CrudService, global_pre_hook: Callable | None, **hook_kwargs: Any) -> dict[str, Any]:
    """Execute the global pre-hook if defined, seeding default model.

    Args:
        service (CrudService): CRUD service supplying default model.
        global_pre_hook (Callable | None): Hook to run before any processing.
        **hook_kwargs (Any): Keyword arguments passed to the hook.

    Returns:
        dict[str, Any]: Possibly modified hook arguments.
    """
    if global_pre_hook:
        model = hook_kwargs.pop("model", None) or service.model
        return global_pre_hook(model=model, **hook_kwargs)
    return hook_kwargs


def _pre_process(service: CrudService, pre_hook: Callable | None, **hook_kwargs: Any) -> dict[str, Any]:
    """Run the pre-hook allowing mutation of incoming arguments.

    Args:
        service (CrudService): CRUD service supplying default model.
        pre_hook (Callable | None): Hook executed before the action.
        **hook_kwargs (Any): Keyword arguments passed to the hook.

    Returns:
        dict[str, Any]: Processed hook arguments.
    """
    if pre_hook:
        model = hook_kwargs.pop("model", None) or service.model
        return pre_hook(model=model, **hook_kwargs)
    return hook_kwargs


def _post_process(service: CrudService, post_hook: Callable | None, output: Any, **hook_kwargs: Any) -> Any:
    """Apply a post-hook to the action result.

    Args:
        service (CrudService): CRUD service supplying default model.
        post_hook (Callable | None): Hook executed after the action.
        output (Any): Data returned from the action.
        **hook_kwargs (Any): Keyword arguments passed to the hook.

    Returns:
        Any: Final output after post processing.
    """
    if post_hook:
        model = hook_kwargs.pop("model", None) or service.model
        out_val = post_hook(model=model, output=output, **hook_kwargs).get("output")
        return out_val.get("output") if isinstance(out_val, dict) and "output" in out_val else out_val
    return output


def _route_function_factory(
    service: CrudService,
    action: Callable,
    many: bool,
    global_pre_hook: Callable | None,
    pre_hook: Callable | None,
    post_hook: Callable | None,
    get_field: str | None,
    join_model: type[DeclarativeBase] | None,
    output_schema: Schema | None,
    http_method: str = "GET",
    plugins: PluginManager | None = None,
    relation_name: str | None = None,
) -> Callable:
    """Construct the route function tying together hooks and action.

    Args:
        service (CrudService): CRUD service for the model.
        action (Callable): CRUD operation to execute.
        many (bool): Whether multiple records are expected.
        global_pre_hook (Callable | None): Global pre-hook.
        pre_hook (Callable | None): Pre-hook.
        post_hook (Callable | None): Post-hook.
        get_field (str | None): Field used for lookups.
        join_model (type[DeclarativeBase] | None): Related model for joins.
        output_schema (Schema | None): Schema used for output serialisation.

    Returns:
        Callable: Configured Flask route function.
    """

    def route_function(id: int | None = None, **hook_kwargs: Any) -> Any:
        # Plugin pre-hook
        if plugins:
            ctx = {
                "model": service.model,
                "method": http_method,
                "many": many,
                "id": id,
                "field": get_field,
                "join_model": join_model,
                "output_schema": output_schema,
            }
            upd = plugins.before_model_op(ctx | hook_kwargs)
            if isinstance(upd, dict):
                hook_kwargs.update(upd)

        pre_kwargs = dict(hook_kwargs)
        pre_kwargs.setdefault("id", id)
        pre_kwargs.setdefault("field", get_field)
        pre_kwargs.setdefault("join_model", join_model)
        pre_kwargs.setdefault("output_schema", output_schema)
        pre_kwargs.setdefault("relation_name", relation_name)
        hook_kwargs = _global_pre_process(
            service,
            global_pre_hook,
            **pre_kwargs,
        )
        hook_kwargs = _pre_process(service, pre_hook, **hook_kwargs)
        action_kwargs: dict[str, Any] = {"lookup_val": id} if id else {}
        action_kwargs.update(hook_kwargs)
        action_kwargs["many"] = many
        action_kwargs["data_dict"] = hook_kwargs.get("deserialized_data")
        action_kwargs["join_model"] = hook_kwargs.get("join_model")
        action_kwargs["id"] = hook_kwargs.get("id")
        action_kwargs["model"] = hook_kwargs.get("model")
        action_kwargs["relation_name"] = hook_kwargs.get("relation_name")
        action_kwargs["http_method"] = http_method

        output = action(**action_kwargs) or abort(404)
        final_output = _post_process(service, post_hook, output, **hook_kwargs)

        # Plugin post-hook
        if plugins:
            ctx_after = {
                "model": hook_kwargs.get("model", service.model),
                "method": http_method,
                "many": many,
                "id": id,
                "field": get_field,
                "join_model": join_model,
                "output_schema": output_schema,
            }
            maybe = plugins.after_model_op(ctx_after | hook_kwargs, final_output)
            if maybe is not None:
                final_output = maybe

        # Attempt to broadcast change events to WS subscribers
        try:
            from flarchitect.core.websockets import broadcast_change

            broadcast_change(
                model=hook_kwargs.get("model", service.model),
                method=http_method,
                payload=final_output,
                id=id,
                many=many,
            )
        except Exception:
            # best-effort; broadcasting should never break the response
            pass

        return final_output

    return route_function


def create_params_from_rule(model: DeclarativeBase, rule, schema: Schema) -> list[dict[str, Any]]:
    """Generates path parameters from a Flask routing rule.

    Args:
        model (DeclarativeBase): Model to generate path parameters from.
        rule: Rule to generate path parameters from.
        schema (Schema): The schema associated with the rule.

    Returns:
        List[Dict[str, Any]]: List of path parameters with enhanced type checks and descriptions.
    """
    path_params = []

    for argument in rule.arguments:
        name = get_config_or_model_meta("name", model=model, output_schema=schema, default=None)
        if not name:
            name = (model or schema).__name__.replace("Schema", "").replace("schema", "")
        name = convert_case(
            name,
            get_config_or_model_meta("API_SCHEMA_CASE", model=model, default="camel"),
        )

        param_info = {
            "name": argument,
            "in": "path",
            "required": True,
            "description": f"Identifier for the {name} instance.",
            "schema": get_param_schema(rule._converters[argument]),
        }

        path_params.append(param_info)

    return path_params


def create_query_params_from_rule(
    rule,
    methods: set,
    schema: Schema,
    many: bool,
    model: DeclarativeBase,
    custom_query_params: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Generates query parameters from a rule.

    Args:
        rule: Rule to generate query parameters from.
        methods (set): Set of methods to generate query parameters from.
        schema (Schema): Schema to generate query parameters from.
        many (bool): Whether the endpoint returns multiple items.
        model (DeclarativeBase): Model to generate query parameters from.
        custom_query_params (List[Dict[str, Any]]): Custom query parameters to append to the generated query parameters.

    Returns:
        List[Dict[str, Any]]: List of query parameters.
    """
    query_params = generate_delete_query_params(schema, model) if "DELETE" in methods else []

    if "GET" in methods and many:
        query_params.extend(generate_get_query_params(schema, model))

    query_params.extend(generate_additional_query_params(methods, schema, model))

    if custom_query_params is None:
        custom_query_params = []

    if custom_query_params:
        query_params.extend(custom_query_params)

    return query_params


def find_rule_by_function(architect, f: Callable):
    """Gets the path, methods, and path parameters for a function.

    Args:
        architect: The architect object.
        f (Callable): The function to get the path, methods, and path parameters for.

    Returns:
        The rule associated with the function.
    """
    for rule in architect.app.url_map.iter_rules():
        if rule.endpoint.split(".")[-1] == f.__name__:
            return rule
    return None


def create_route_function(
    service,
    method: str,
    many: bool,
    join_model: type[DeclarativeBase] | None = None,
    get_field: str | None = None,
    **kwargs,
) -> Callable:
    """
    Sets up the route function for the API based on the HTTP method.

    Args:
        service: The CRUD service for the model.
        method (str): The HTTP method (GET, POST, PATCH, DELETE).
        many (bool): Whether the route handles multiple records.
        join_model (Optional[Type[DeclarativeBase]]): The model to use in the join.
        get_field (Optional[str]): The field to get the record by.

    Returns:
        Callable: The route function.
    """
    global_pre_hook = get_config_or_model_meta("API_GLOBAL_SETUP_CALLBACK", default=None, method=method)
    pre_hook = get_config_or_model_meta("API_SETUP_CALLBACK", model=service.model, default=None, method=method)
    post_hook = get_config_or_model_meta("API_RETURN_CALLBACK", model=service.model, default=None, method=method)

    action_map = {
        # Preserve repeated query params (e.g., ?join=a&join=b) by using flat=False
        "GET": lambda **action_kwargs: service.get_query(request.args.to_dict(flat=False), alt_field=get_field, **action_kwargs),
        "DELETE": service.delete_object,
        "PATCH": service.update_object,
        "POST": service.add_object,
    }

    action = action_map.get(method)
    return _route_function_factory(
        service,
        action,
        many,
        global_pre_hook,
        pre_hook,
        post_hook,
        get_field,
        join_model,
        kwargs.get("output_schema"),
        method,
        plugins=kwargs.get("plugins"),
        relation_name=kwargs.get("relation_name"),
    )


class RouteCreator(AttributeInitialiserMixin):
    """Automatically construct API routes for configured models.

    RouteCreator inspects SQLAlchemy models and their associated schemas to
    generate CRUD endpoints. When ``api_full_auto`` is ``True``, initialisation
    triggers model setup, configuration validation, and registration of the
    generated routes on the application blueprint.

    Attributes:
        created_routes: Mapping of endpoint names to route metadata.
        architect: Parent Architect supplying the Flask application.
        api_full_auto: Enables automatic route generation during initialisation.
        api_base_model: Base model or models used to discover resources.
        api_base_schema: Default schema used for serialisation.
        db_service: CRUD service class used for database interactions.
        session: SQLAlchemy session or sessions bound to the models.
        blueprint: Flask blueprint where generated routes are registered.
    """

    created_routes: dict[str, dict[str, Any]] | None = None
    architect: Architect
    api_full_auto: bool | None = True
    api_base_model: Callable | list[Callable] | None = None
    api_base_schema: Callable | None = None
    db_service: Callable | None = CrudService
    session: Session | list[Session] | None = None
    blueprint: Blueprint | None = None

    def __init__(self, architect: Architect, *args, **kwargs):
        """Initialise the RouteCreator object.

        Args:
            architect (Architect): The architect object.
            *args (list): List of arguments.
            **kwargs (dict): Dictionary of keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.architect = architect
        self.created_routes: dict[str, dict[str, Any]] = {}
        if self.api_full_auto:
            self.setup_models()
            self.validate()
            self.setup_api_routes()

    def setup_models(self):
        """Set up the models for the API by adding necessary configurations."""
        self.api_base_model = [self.api_base_model] if not isinstance(self.api_base_model, list) else self.api_base_model

        for base in self.api_base_model:
            for _ in base.__subclasses__():
                # Add any necessary setup here for model_class
                pass

    def validate(self):
        """Validate the RiceAPI configuration."""
        if self.api_full_auto:
            self._validate_base_model_setup()
            self._validate_authentication_setup()
            self._validate_soft_delete_setup()

    def _validate_base_model_setup(self):
        """Validate the base model setup for the API."""
        if not self.api_base_model:
            raise ValueError("If FULL_AUTO is True, API_BASE_MODEL must be set to a SQLAlchemy model.")

        self.api_base_model = [self.api_base_model] if not isinstance(self.api_base_model, list) else self.api_base_model

        for base in self.api_base_model:
            try:
                with get_session(base):
                    pass
            except Exception as exc:  # pragma: no cover - configuration error
                raise ValueError(
                    "If FULL_AUTO is True, API_BASE_MODEL must be bound to a SQLAlchemy session.",
                ) from exc

    def _validate_authentication_setup(self):
        """Validate the authentication setup for the API."""
        user = get_config_or_model_meta("API_USER_MODEL", default=None)
        auth_method = get_config_or_model_meta("API_AUTHENTICATE_METHOD", default=None)
        authenticate = get_config_or_model_meta("API_AUTHENTICATE", default=False)
        custom_auth = get_config_or_model_meta("API_CUSTOM_AUTH", default=False)
        hash_field = get_config_or_model_meta("API_CREDENTIAL_HASH_FIELD", default=None)
        check_method = get_config_or_model_meta("API_KEY_AUTH_AND_RETURN_METHOD", default=None)

        if not self.architect.app.config.get("SECRET_KEY") and auth_method:
            raise ValueError(f"SECRET_KEY must be set in the Flask app config. You can use this randomly generated key:\n{secrets.token_urlsafe(48)}\nAnd this SALT key\n{secrets.token_urlsafe(32)}\n")

        if auth_method and "custom" not in auth_method and not user:
            raise ValueError("If API_AUTHENTICATE_METHOD is set to a callable, API_USER_MODEL must be set to the user model.")

        if authenticate and not auth_method:
            raise ValueError("If API_AUTHENTICATE is set to True, API_AUTHENTICATE_METHOD must be set to either 'basic', 'jwt', 'api_key' or custom.")

        if authenticate and "jwt" in auth_method:
            ACCESS_SECRET_KEY = os.environ.get("ACCESS_SECRET_KEY") or self.architect.app.config.get("ACCESS_SECRET_KEY")
            REFRESH_SECRET_KEY = os.environ.get("REFRESH_SECRET_KEY") or self.architect.app.config.get("REFRESH_SECRET_KEY")
            if not ACCESS_SECRET_KEY or not REFRESH_SECRET_KEY:
                raise ValueError(
                    """If API_AUTHENTICATE_METHOD is set to 'jwt' you must set ACCESS_SECRET_KEY and REFRESH_SECRET_KEY in the
                    Flask app config or as environment variables."""
                )

        if authenticate and "api_key" in auth_method:
            if not user:
                raise ValueError("If API_AUTHENTICATE_METHOD is set to 'api_key', API_USER_MODEL must be set to the user model.")
            if not hash_field or not check_method:
                raise ValueError(
                    "If API_AUTHENTICATE_METHOD is set to 'api_key', API_CREDENTIAL_HASH_FIELD must be set "
                    "to the name of the models field that holds the hashed API key \n\n"
                    "hash fields "
                    ""
                    ""
                    "which must use  OR a valid API_KEY_AUTH_AND_RETURN_METHOD callable that validates the key and returns the user model must be supplied."
                )

        if authenticate and "custom" in auth_method:
            if not custom_auth:
                raise ValueError("If API_AUTHENTICATE_METHOD is set to 'custom', API_CUSTOM_AUTH must be set to True.")
            if not callable(custom_auth):
                raise ValueError("If API_AUTHENTICATE_METHOD is set to 'custom', API_CUSTOM_AUTH must be a callable that takes the request and returns a user object.")

    def _validate_soft_delete_setup(self):
        """Validate the soft delete setup for the API."""
        soft_delete = get_config_or_model_meta("API_SOFT_DELETE", default=False)
        if soft_delete:
            deleted_attr = get_config_or_model_meta("API_SOFT_DELETE_ATTRIBUTE", default=None)
            soft_delete_values = get_config_or_model_meta("API_SOFT_DELETE_VALUES", default=None)

            if not deleted_attr:
                raise ValueError("If API_SOFT_DELETE is set to True, API_SOFT_DELETE_ATTRIBUTE must be set to the name of the attribute that holds the soft delete value.")

            if not soft_delete_values or not isinstance(soft_delete_values, tuple) or len(soft_delete_values) != 2:
                raise ValueError("API_SOFT_DELETE_VALUES must be a tuple of two values that represent the soft delete state (not deleted, deleted).")

    def setup_api_routes(self):
        """Setup all necessary API routes."""
        self.make_auth_routes()
        self.create_api_blueprint()
        self.create_routes()
        self._create_schema_discovery_route()
        self._create_docs_bundle_route()
        self.make_exception_routes()
        self.architect.app.register_blueprint(self.blueprint)

    def make_exception_routes(self):
        """Register error handlers for standard and custom HTTP exceptions."""

        logger.debug(
            4,
            "Setting up custom error handler for CustomHTTPException.",
        )
        self.architect.app.register_error_handler(CustomHTTPException, handle_http_exception)

        for code in default_exceptions:
            logger.debug(
                4,
                f"Setting up custom error handler for blueprint |{self.blueprint.name}| with http code +{code}+.",
            )
            self.architect.app.register_error_handler(code, handle_http_exception)

    def _create_schema_discovery_route(self) -> None:
        """Expose a discovery endpoint enumerating filters and relationships."""

        path = self.architect.get_config("API_SCHEMA_DISCOVERY_ROUTE", "/schema/discovery")
        if not path:
            return

        for rule in self.architect.app.url_map.iter_rules():  # pragma: no cover - simple guard
            if str(rule.rule) == path and "GET" in (rule.methods or set()):
                return

        require_auth = bool(self.architect.get_config("API_SCHEMA_DISCOVERY_AUTH", True))
        max_depth_default = self.architect.get_config("API_SCHEMA_DISCOVERY_MAX_DEPTH", 2) or 2
        try:
            max_depth_default = int(max_depth_default)
        except (TypeError, ValueError):
            max_depth_default = 2

        roles_spec = self.architect.get_config("API_SCHEMA_DISCOVERY_ROLES", None)
        roles_any_of = bool(self.architect.get_config("API_SCHEMA_DISCOVERY_ROLES_ANY_OF", False))

        decorator_kwargs: dict[str, Any] = {
            "output_schema": None,
            "auth": require_auth,
            "many": False,
            "group_tag": "Schema Discovery",
            "tag": "Schema Discovery",
            "summary": "List filters, operators, and relationships available for models.",
        }

        if roles_spec:
            decorator_kwargs["roles"] = roles_spec
        if roles_spec and roles_any_of:
            decorator_kwargs["roles_any_of"] = True

        @self.architect.app.route(path, methods=["GET"])
        @self.architect.schema_constructor(**decorator_kwargs)
        def schema_discovery() -> dict[str, Any]:
            query = request.args
            model_param = query.get("model")
            depth_param = query.get("depth", type=int)

            model_filter = None
            if model_param:
                tokens = {
                    token.strip().lower()
                    for token in model_param.split(",")
                    if token and token.strip()
                }
                model_filter = tokens or None

            depth = max_depth_default
            if isinstance(depth_param, int) and depth_param > 0:
                depth = depth_param

            created_routes = getattr(self, "created_routes", {}) or {}
            model_classes: set[type] = set()
            for info in created_routes.values():
                mdl = info.get("model")
                if mdl is not None:
                    model_classes.add(mdl)

            base_models = self.api_base_model or []
            if not isinstance(base_models, (list, tuple)):
                base_models = [base_models]
            for base in base_models:
                if base is None:
                    continue
                model_classes.add(base)
                model_classes.update(base.__subclasses__())

            payload = build_schema_discovery_payload(
                models=model_classes,
                created_routes=created_routes,
                model_filter=model_filter,
                max_depth=depth,
            )
            return payload

    def _create_docs_bundle_route(self) -> None:
        """Expose a documentation bundle endpoint merging auto and manual routes."""

        path = self.architect.get_config("API_DOCS_BUNDLE_ROUTE", "/docs/bundle")
        if not path:
            return

        for rule in self.architect.app.url_map.iter_rules():  # pragma: no cover - simple guard
            if str(rule.rule) == path and "GET" in (rule.methods or set()):
                return

        require_auth = bool(self.architect.get_config("API_DOCS_BUNDLE_AUTH", True))
        roles_spec = self.architect.get_config("API_DOCS_BUNDLE_ROLES", None)
        roles_any_of = bool(self.architect.get_config("API_DOCS_BUNDLE_ROLES_ANY_OF", False))

        decorator_kwargs: dict[str, Any] = {
            "output_schema": None,
            "auth": require_auth,
            "many": False,
            "group_tag": "Documentation",
            "tag": "Documentation",
            "summary": "Merge auto-generated and custom route metadata.",
        }

        if roles_spec:
            decorator_kwargs["roles"] = roles_spec
        if roles_spec and roles_any_of:
            decorator_kwargs["roles_any_of"] = True

        @self.architect.app.route(path, methods=["GET"])
        @self.architect.schema_constructor(**decorator_kwargs)
        def docs_bundle() -> dict[str, Any]:
            return build_docs_bundle(
                app=self.architect.app,
                route_spec=self.architect.route_spec,
                created_routes=self.created_routes,
            )

    def create_routes(self):
        """Create all the routes for the API."""
        for base in self.api_base_model:
            for model_class in base.__subclasses__():
                if hasattr(model_class, "__table__") and hasattr(model_class, "Meta"):
                    with get_session(model_class) as session:
                        self.make_all_model_routes(model_class, session)
                else:
                    logger.debug(
                        4,
                        f"Skipping model |{model_class.__name__}| because it does not have a table or Meta class.",
                    )

    # ----- Roles resolution helpers -----
    def _normalize_roles_spec(self, spec: Any, default_any_of: bool = False) -> tuple[list[str] | None, bool]:
        """Normalise a roles specification to a concrete list and any_of flag.

        Args:
            spec: Roles definition which may be a list/tuple/str/dict/bool.
            default_any_of: Fallback for ``any_of`` when not declared.

        Returns:
            Tuple of (roles list or None, any_of flag).
        """
        if spec is None:
            return None, False
        if spec is True:
            # True means "auth only"; we don't attach a role decorator
            return None, default_any_of
        if isinstance(spec, list | tuple):
            return list(spec), default_any_of
        if isinstance(spec, str):
            return [spec], default_any_of
        if isinstance(spec, dict):
            roles = spec.get("roles", [])
            any_of = bool(spec.get("any_of", default_any_of))
            if isinstance(roles, str):
                roles = [roles]
            if isinstance(roles, list | tuple) and roles:
                return list(roles), any_of
            return None, any_of
        return None, default_any_of

    def _resolve_roles_for_route(
        self,
        *,
        model: Callable | None,
        http_method: str,
        is_many: bool = False,
        is_relation: bool = False,
    ) -> tuple[list[str] | None, bool]:
        """Resolve roles and any_of for a specific route from config/metadata.

        Order of precedence:
        1) ``API_ROLE_MAP`` (dict or list/str) on model or app config.
           - Keys checked in order: relation-specific → GET granularity → method → ALL → *
           - Values can be list[str], str, or {roles: [...], any_of: bool}.
        2) ``API_ROLES_REQUIRED`` (list) → all-of semantics.
        3) ``API_ROLES_ACCEPTED`` (list) → any-of semantics.
        """
        role_map = get_config_or_model_meta("API_ROLE_MAP", model=model, default=None)
        if role_map is not None:
            keys: list[str] = []
            method = http_method.upper()
            if is_relation:
                keys.append(f"RELATION_{method}")
                if method == "GET":
                    keys.append("RELATION_GET_MANY" if is_many else "RELATION_GET_ONE")
            if method == "GET":
                keys.append("GET_MANY" if is_many else "GET_ONE")
            keys.append(method)
            keys.extend(["ALL", "*"])

        if isinstance(role_map, dict):
            for k in keys:
                if k in role_map:
                    return self._normalize_roles_spec(role_map[k])
        else:
            return self._normalize_roles_spec(role_map)

        required = get_config_or_model_meta("API_ROLES_REQUIRED", model=model, default=None)
        if required is not None:
            return self._normalize_roles_spec(required, default_any_of=False)

        accepted = get_config_or_model_meta("API_ROLES_ACCEPTED", model=model, default=None)
        if accepted is not None:
            return self._normalize_roles_spec(accepted, default_any_of=True)

        return None, False

    def make_auth_routes(self):
        """Create the authentication routes for the API.

        Honours ``API_AUTO_AUTH_ROUTES`` (default True). When disabled, no
        built‑in auth routes are registered. Supports ``API_AUTHENTICATE_METHOD``
        as a string or a list of methods. Normalises values to lower‑case.
        """
        auto = get_config_or_model_meta("API_AUTO_AUTH_ROUTES", default=True)
        if not auto:
            return

        methods_cfg = get_config_or_model_meta("API_AUTHENTICATE_METHOD", default=None)
        user = get_config_or_model_meta("API_USER_MODEL", default=None)

        if not methods_cfg:
            return

        # Normalise to a list[str] of lower‑case methods
        if isinstance(methods_cfg, (list, tuple, set)):
            auth_methods = [str(m).lower() for m in methods_cfg]
        else:
            auth_methods = [str(methods_cfg).lower()]

        from flask_login import LoginManager

        login_manager = LoginManager()
        login_manager.init_app(self.architect.app)

        if "jwt" in auth_methods:
            self._make_jwt_auth_routes(user)
        elif "basic" in auth_methods:
            self._make_basic_auth_routes(user)
        elif "api_key" in auth_methods:
            self._make_api_key_auth_routes(user)

        # Provide /auth/me for any supported authentication method when
        # a user model is configured (including custom auth).
        if user is not None and bool(get_config_or_model_meta("API_EXPOSE_ME", default=True)):
            self._create_me_route(user)

        @login_manager.user_loader
        def load_user(user_id):
            return user.get(user_id)

    def _make_basic_auth_routes(self, user: Callable) -> None:
        """Create basic authentication login route.

        This route validates the ``Authorization`` header using HTTP Basic
        credentials. When authentication succeeds, basic user details are
        returned to the client. No user context is persisted after the request.
        """

        @self.architect.app.route("/auth/login", methods=["POST"])
        def basic_login() -> dict[str, Any]:
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Basic "):
                return create_response(status=401, errors={"error": "Invalid credentials"})

            try:
                encoded = auth_header.split(" ", 1)[1]
                username, password = base64.b64decode(encoded).decode("utf-8").split(":", 1)
            except (
                ValueError,
                binascii.Error,
                UnicodeDecodeError,
            ):  # pragma: no cover - bad header
                return create_response(status=401, errors={"error": "Invalid credentials"})

            lookup_field = get_config_or_model_meta("API_USER_LOOKUP_FIELD", model=user, default=None)
            check_method = get_config_or_model_meta("API_CREDENTIAL_CHECK_METHOD", model=user, default=None)
            usr = user.query.filter(getattr(user, lookup_field) == username).first()

            if usr and getattr(usr, check_method)(password):
                pk, lookup = _get_pk_and_lookups()
                return create_response({"user_pk": getattr(usr, pk), lookup: getattr(usr, lookup)})

            return create_response(status=401, errors={"error": "Invalid credentials"})

    def _make_api_key_auth_routes(self, user: Callable) -> None:
        """Register the API key authentication login endpoint.

        Args:
            user (Callable): User model containing credential fields and
                verification methods.

        Returns:
            None: The login route is attached to the Flask application.
        """

        @self.architect.app.route("/auth/login", methods=["POST"])
        def api_key_login() -> dict[str, Any]:
            header = request.headers.get("Authorization", "")
            scheme, _, token = header.partition(" ")
            if scheme.lower() != "api-key" or not token:
                return create_response(status=401, errors={"error": "Invalid credentials"})

            custom_method = get_config_or_model_meta("API_KEY_AUTH_AND_RETURN_METHOD", model=user, default=None)
            if callable(custom_method):
                usr = custom_method(token)
            else:
                hash_field = get_config_or_model_meta("API_CREDENTIAL_HASH_FIELD", model=user, default=None)
                check_method = get_config_or_model_meta("API_CREDENTIAL_CHECK_METHOD", model=user, default=None)

                query = getattr(user, "query", None)
                usr = None
                if query is None:
                    try:
                        with get_session(user) as session:
                            for candidate in session.query(user).all():
                                stored = getattr(candidate, hash_field, None)
                                if stored and getattr(candidate, check_method)(token):
                                    usr = candidate
                                    break
                    except Exception:
                        usr = None
                else:
                    for candidate in query.all():
                        stored = getattr(candidate, hash_field, None)
                        if stored and getattr(candidate, check_method)(token):
                            usr = candidate
                            break

            if usr:
                pk, lookup = _get_pk_and_lookups()
                data: dict[str, Any] = {"user_pk": getattr(usr, pk)}
                if lookup:
                    data[lookup] = getattr(usr, lookup)
                return create_response(data)

            return create_response(status=401, errors={"error": "Invalid credentials"})

    def _make_jwt_auth_routes(self, user: Callable) -> None:
        """Register JWT login, logout, and refresh endpoints.

        Args:
            user (Callable): User model used for credential verification and
                token generation.

        Returns:
            None: Routes are added to the Flask application.
        """
        self._create_jwt_login_route(user)
        self._create_jwt_logout_route(user)
        self._create_jwt_refresh_route(user)

    def _create_me_route(self, user: Callable) -> None:
        """Create the authenticated "me" route to return the current user.

        Registers ``GET /auth/me`` which returns the authenticated user serialised
        with the model's output schema. This endpoint requires authentication and
        is available for any enabled auth method when a user model is configured.
        """

        # Avoid duplicate registration if a GET rule already exists for path
        path = get_config_or_model_meta("API_AUTH_ME_ROUTE", default="/auth/me")
        for rule in self.architect.app.url_map.iter_rules():  # pragma: no cover - simple iteration
            if str(rule.rule) == path and "GET" in (rule.methods or set()):
                return

        # Build an output schema for the user model
        _, out_schema = get_input_output_from_model_or_make(user)

        @self.architect.app.route(path, methods=["GET"])
        @self.architect.schema_constructor(
            output_schema=out_schema,
            model=user,
            many=False,
            group_tag="Authentication",
            tag="Authentication",
            summary="Return current authenticated user.",
            error_responses=[401],
        )
        def me(*args, **kwargs):
            usr = get_current_user()
            if not usr:
                raise CustomHTTPException(401, "Unauthorized")
            return usr

    def _create_jwt_login_route(self, user: Callable) -> None:
        """Create the login route for JWT authentication.

        Args:
            user (Callable): User model that provides credential lookup and
                verification methods.

        Returns:
            None: The login route is registered on the Flask application.
        """

        @self.architect.app.route("/auth/login", methods=["POST"])
        @self.architect.schema_constructor(
            input_schema=LoginSchema,
            output_schema=TokenSchema,
            model=user,
            many=False,
            roles=True,
            group_tag="Authentication",
            tag="Authentication",
            summary="Authenticate user and return JWT tokens.",
            auth=False,
            error_responses=[401],
        )
        def login(*args, **kwargs):
            """Authenticate a user and return JWT tokens."""

            data = request.get_json()
            username = data.get("username")
            password = data.get("password")

            # The hash_field is retrieved for future use but not needed here
            get_config_or_model_meta("API_CREDENTIAL_HASH_FIELD", model=user, default=None)
            lookup_field = get_config_or_model_meta("API_USER_LOOKUP_FIELD", model=user, default=None)
            check_method = get_config_or_model_meta("API_CREDENTIAL_CHECK_METHOD", model=user, default=None)

            usr = user.query.filter(getattr(user, lookup_field) == username).first()

            if usr and getattr(usr, check_method)(password):
                access_token = _generate_access_token(usr)
                refresh_token = _generate_refresh_token(usr)

                pk, lookup_field = _get_pk_and_lookups()

                return {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user_pk": getattr(usr, pk),
                }

            raise CustomHTTPException(401, "Invalid credentials")

    def _create_jwt_logout_route(self, user: Callable) -> None:
        """Create the logout route for JWT authentication.

        Args:
            user (Callable): User model, included for interface consistency.

        Returns:
            None: The logout route is registered on the Flask application.
        """

        @self.architect.app.route("/auth/logout", methods=["POST"])
        @self.architect.schema_constructor(
            output_schema=None,
            many=False,
            group_tag="Authentication",
            tag="Authentication",
            summary="Log out current user.",
        )
        def logout(*args, **kwargs):
            """Log out the current user."""

            set_current_user(None)
            return {}

    def _create_jwt_refresh_route(self, user: Callable) -> None:
        """Create the refresh token route for JWT authentication.

        Args:
            user (Callable): User model, currently unused but kept for API
                symmetry with other JWT route creators.

        Returns:
            None: The refresh route is registered on the Flask application.
        """

        # Configurable path with safe default
        path = get_config_or_model_meta("API_AUTH_REFRESH_ROUTE", default="/auth/refresh")

        # Avoid duplicate registration if a POST rule already exists for path
        for rule in self.architect.app.url_map.iter_rules():  # pragma: no cover - simple iteration
            if str(rule.rule) == str(path) and "POST" in (rule.methods or set()):
                return

        def refresh(*args, **kwargs):
            """Refresh a JWT access token using a refresh token."""

            # Extract the refresh token from the request
            refresh_token = request.get_json().get("refresh_token")
            # Normalise in case clients send "Bearer <token>" in the payload
            if isinstance(refresh_token, str) and refresh_token.lower().startswith("bearer "):
                refresh_token = refresh_token.split(" ", 1)[1].strip()
            if not refresh_token:
                raise CustomHTTPException(status_code=400, reason="Refresh token is missing")

            # Attempt to refresh the access token and retrieve the user
            try:
                new_access_token, user = _refresh_access_token(refresh_token)
            except CustomHTTPException as e:
                # Let your application's error handlers manage the response
                raise e

            # Generate a new refresh token and rotate the old one (single-use)
            new_refresh_token = _generate_refresh_token(user)
            import contextlib
            with contextlib.suppress(Exception):
                # Rotation is best-effort; failure should not expose the old token
                rotate_refresh_token(refresh_token, new_refresh_token)

            pk, lookup_field = _get_pk_and_lookups()
            # Return the new tokens
            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "user_pk": getattr(user, pk),
            }

        # Apply schema/metadata wrapper and register dynamically to honour path
        wrapped = self.architect.schema_constructor(
            input_schema=RefreshSchema,
            output_schema=TokenSchema,
            many=False,
            group_tag="Authentication",
            tag="Authentication",
            summary="Refresh access token.",
            auth=False,
            error_responses=[400, 401, 403],
        )(refresh)

        # Unique endpoint name stable across re-runs; add only once above
        self.architect.app.add_url_rule(path, endpoint=wrapped.__name__, view_func=wrapped, methods=["POST"])

    def create_api_blueprint(self):
        """Register the API blueprint and error handlers."""
        api_prefix = get_config_or_model_meta("API_PREFIX", default="/api")
        self.blueprint = Blueprint("api", __name__, url_prefix=api_prefix)

        @self.architect.app.before_request
        def before_request(*args, **kwargs):
            g.start_time = time.time()

    def make_all_model_routes(self, model: Callable, session: Any) -> None:
        """Create all routes for a given model.

        Args:
            model (Callable): The model to create routes for.
            session (Any): Database session used for operations on the model.

        Returns:
            None: Routes for the model and its relations are registered.
        """
        self._generate_relation_routes(model, session)
        self._generate_model_routes(model, session)

    def _generate_model_routes(self, model: Callable, session: Any) -> None:
        """Generate CRUD routes for a model.

        Args:
            model (Callable): The model to create routes for.
            session (Any): Database session to use for the model.

        Returns:
            None: CRUD endpoints are generated for the provided model.
        """

        # Retrieve allowed and blocked methods from configuration or model metadata

        read_only = get_config_or_model_meta("API_READ_ONLY", model=model, default=False)

        register_canonical_val = get_config_or_model_meta(
            "API_REGISTER_CANONICAL_ROUTES",
            model=model,
            default=True,
        )
        if isinstance(register_canonical_val, str):
            register_canonical = register_canonical_val.strip().lower() not in {"0", "false", "no"}
        else:
            register_canonical = bool(register_canonical_val)

        extra_endpoint_cfg = get_config_or_model_meta("endpoint", model=model, default=None)
        extra_segments: list[str] = []
        if isinstance(extra_endpoint_cfg, str):
            extra_segments = [extra_endpoint_cfg]
        elif isinstance(extra_endpoint_cfg, (list, tuple, set)):
            extra_segments = [str(item) for item in extra_endpoint_cfg if item is not None]
        elif extra_endpoint_cfg:
            extra_segments = [str(extra_endpoint_cfg)]

        input_schema_class, output_schema_class = get_input_output_from_model_or_make(model)
        canonical_segment = self._get_url_naming_function(model, input_schema_class, output_schema_class).strip("/")

        route_segments: list[str] = []
        if register_canonical:
            route_segments.append(canonical_segment)

        for seg in extra_segments:
            norm = str(seg).strip("/")
            if not norm:
                continue
            if norm not in route_segments:
                route_segments.append(norm)

        # Ensure ``to_url`` helpers remain available even when canonical routes are skipped so
        # relation serializers and manual handlers can continue to reference them. Prefer the
        # first registered segment (canonical when enabled, otherwise the first alternate).
        to_url_segment = canonical_segment if register_canonical else (route_segments[0] if route_segments else canonical_segment)
        self._add_self_url_function_to_model(model, endpoint_segment=to_url_segment)

        allowed, allowed_from = get_config_or_model_meta("API_ALLOWED_METHODS", model=model, default=[], return_from_config=True)
        allowed_methods = [x.upper() for x in allowed]

        blocked_methods, blocked_from = get_config_or_model_meta(
            "API_BLOCK_METHODS",
            model=model,
            default=[],
            allow_join=True,
            return_from_config=True,
        )
        blocked_methods = [x.upper() for x in blocked_methods]

        if not route_segments:
            return

        for http_method in ["GETS", "GET", "POST", "PATCH", "DELETE"]:
            if read_only and http_method in ["POST", "PATCH", "DELETE"] and (http_method not in allowed_methods):
                continue

            check_http_meth = http_method if not http_method.endswith("S") else http_method.replace("S", "")
            if check_http_meth in blocked_methods and blocked_from == "config" and allowed_from == "default":
                continue

            if check_http_meth not in allowed_methods and allowed_from == "config":
                continue

            if check_http_meth in blocked_methods and blocked_from == "model":
                continue
            if check_http_meth in blocked_methods and (check_http_meth not in allowed_methods and allowed_from == "model"):
                continue

            if check_http_meth not in allowed_methods and allowed_methods and allowed_from in ["config", "default"]:
                continue

            if allowed_methods and allowed_from == "model" and check_http_meth not in allowed_methods:
                continue

            for segment in route_segments:
                route_data = self._prepare_route_data(
                    model,
                    session,
                    http_method,
                    endpoint=segment,
                    input_schema_class=input_schema_class,
                    output_schema_class=output_schema_class,
                    canonical_segment=canonical_segment,
                )
                self.generate_route(**route_data)

    def _generate_relation_routes(self, model: Callable, session: Any) -> None:
        """Generate routes for model relationships if configured.

        Args:
            model (Callable): The model to create relation routes for.
            session (Any): Database session to use for the model.

        Returns:
            None: Relation endpoints are generated when enabled.
        """
        if get_config_or_model_meta("API_ADD_RELATIONS", model=model, default=True):
            relations = get_models_relationships(model)
            for relation_data in relations:
                prepared_relation_data = self._prepare_relation_route_data(relation_data, session)
                self._create_relation_route_and_to_url_function(prepared_relation_data)

    def _create_relation_route_and_to_url_function(self, relation_data: dict[str, Any]) -> None:
        """Create a route for a relation and attach a ``to_url`` helper.

        Args:
            relation_data (dict[str, Any]): Data describing the relation,
                including models and join keys.

        Returns:
            None: The route is registered and helper added to the child model.
        """
        child = relation_data["child_model"]
        parent = relation_data["parent_model"]
        self._add_relation_url_function_to_model(
            child=child,
            parent=parent,
            id_key=relation_data["join_key"],
            relation_name=relation_data.get("relation_name"),
            relation_url_segment=relation_data.get("relation_url_segment"),
        )
        self.generate_route(**relation_data)

    def _prepare_route_data(
        self,
        model: Callable,
        session: Any,
        http_method: str,
        *,
        endpoint: str | None = None,
        input_schema_class: type[Schema] | None = None,
        output_schema_class: type[Schema] | None = None,
        canonical_segment: str | None = None,
    ) -> dict[str, Any]:
        """Prepare data for creating a route.

        Args:
            model (Callable): The model to create the route for.
            session (Any): The database session to use for the model.
            http_method (str): The HTTP method for the route.

        Returns:
            Dict[str, Any]: The prepared route data.
        """

        many = False
        if http_method == "GETS":
            many = True
            http_method = "GET"

        if input_schema_class is None or output_schema_class is None:
            input_schema_class, output_schema_class = get_input_output_from_model_or_make(model)

        canonical_segment = (canonical_segment or self._get_url_naming_function(model, input_schema_class, output_schema_class)).strip("/")
        segment = endpoint.strip("/") if isinstance(endpoint, str) else canonical_segment
        segment = segment or canonical_segment

        base_url = f"/{segment}"
        method = http_method

        if http_method == "GET" and not many or http_method in ["DELETE", "PATCH"]:
            pk_url = get_url_pk(model)  # GET operates on a single item, so include the primary key in the URL
            base_url = f"{base_url}/{pk_url}"

        logger.debug(
            4,
            f"Collecting main model data for --{model.__name__}-- with expected url |{method}|:`{base_url}`.",
        )

        # Resolve roles config for this route
        roles_list, roles_any_of = self._resolve_roles_for_route(
            model=model,
            http_method=http_method,
            is_many=many,
            is_relation=False,
        )

        route_name = model.__name__.lower()
        if segment != canonical_segment:
            suffix = segment.replace("/", "_")
            route_name = f"{route_name}__{suffix}" if suffix else route_name

        return {
            "model": model,
            "many": many,
            "method": method,
            "url": base_url,
            "name": route_name,
            "url_segment": segment,
            "output_schema": output_schema_class,
            "session": session,
            "input_schema": (input_schema_class if http_method in ["POST", "PATCH"] else None),
            # Attach roles for schema_constructor if configured
            "roles": roles_list if roles_list else False,
            "roles_any_of": roles_any_of if roles_list else False,
        }

    def _prepare_relation_route_data(self, relation_data: dict[str, Any], session: Any) -> dict[str, Any]:
        """Prepare data for creating a relation route.

        Args:
            relation_data (Dict[str, Any]): Data about the relation.
            session (Any): The database session to use for the relation.

        Returns:
            Dict[str, Any]: The prepared relation route data.
        """

        child_model = relation_data["model"]
        parent_model = relation_data["parent"]
        input_schema_class, output_schema_class = get_input_output_from_model_or_make(child_model)
        pinput_schema_class, poutput_schema_class = get_input_output_from_model_or_make(parent_model)

        key = get_primary_key_info(parent_model)

        parent_endpoint = self._get_url_naming_function(parent_model, pinput_schema_class, poutput_schema_class)
        child_endpoint = self._get_url_naming_function(child_model, input_schema_class, output_schema_class)

        # Resolve naming strategy for relation route
        relation_key = relation_data.get("relationship") or relation_data.get("relation_name")
        naming_mode = self._resolve_relation_route_naming(parent_model, child_model)
        # Optional alias map (applies to URL segment only when relationship-based)
        alias_map = get_config_or_model_meta("RELATION_ROUTE_MAP", model=parent_model, default={}) or {}
        alias = alias_map.get(relation_key)
        if naming_mode == "relationship":
            final_segment = alias or relation_key
        elif naming_mode == "auto":
            # Check for potential collision using model-based segment; if collision, use relationship key
            if self._would_model_segment_collide(parent_model, child_model, child_endpoint):
                final_segment = alias or relation_key
                naming_mode = "relationship"  # document effective choice
            else:
                final_segment = child_endpoint
        else:
            final_segment = child_endpoint

        relation_url = (
            f"/{parent_endpoint}"
            f"/<{key[1]}:{key[0]}>"
            f"/{final_segment}"
        )
        logger.debug(
            4,
            f"Collecting parent/child model relationship for --{parent_model.__name__}-- and --{child_model.__name__}-- with expected url `{relation_url}`.",
        )

        # Resolve roles for relation route (child inherits role policy by default)
        roles_list, roles_any_of = self._resolve_roles_for_route(
            model=child_model,
            http_method="GET",
            is_many=(relation_data["join_type"][-4:].lower() == "many" or relation_data.get("many", False)),
            is_relation=True,
        )

        return {
            "child_model": child_model,
            "model": child_model,
            "parent_model": parent_model,
            "many": relation_data["join_type"][-4:].lower() == "many" or relation_data.get("many", False),
            "method": "GET",
            # Keep raw relation key for idempotent function naming suffix
            "relation_name": relation_key,
            # Expose the URL segment actually used for to_url helper
            "relation_url_segment": final_segment,
            "url": relation_url,
            # Ensure internal route name uniqueness by including relation key (idempotent)
            "name": self._compose_relation_route_name(child_model, parent_model, relation_key),
            "join_key": relation_data["right_column"],
            "output_schema": output_schema_class,
            "session": session,
            # Attach roles for schema_constructor if configured
            "roles": roles_list if roles_list else False,
            "roles_any_of": roles_any_of if roles_list else False,
        }

    def _compose_relation_route_name(self, child_model: Callable, parent_model: Callable, relation_key: str) -> str:
        base = f"{child_model.__name__.lower()}_join_to_{parent_model.__name__.lower()}"
        suffix = f"_{relation_key}" if not base.endswith(f"_{relation_key}") else ""
        return base + suffix

    def _resolve_relation_route_naming(self, parent_model: Callable, child_model: Callable) -> str:
        # Per-model Meta has priority
        model_pref = get_config_or_model_meta("RELATION_ROUTE_NAMING", model=parent_model, default=None)
        if model_pref in {"model", "relationship", "auto"}:
            return model_pref
        # Global config
        global_pref = get_config_or_model_meta("API_RELATION_ROUTE_NAMING", default=None)
        if global_pref in {"model", "relationship", "auto"}:
            return global_pref
        # Back-compat: translate legacy API_RELATION_URL_STYLE
        legacy = get_config_or_model_meta("API_RELATION_URL_STYLE", default=None)
        if legacy == "relation-key":
            return "relationship"
        if legacy == "target-model":
            return "model"
        # Default: model-based naming for backward compatibility
        return "model"

    def _would_model_segment_collide(self, parent_model: Callable, child_model: Callable, child_endpoint: str) -> bool:
        # If multiple relationships from parent -> same child, then child_endpoint would collide
        try:
            rels = get_models_relationships(parent_model)
        except Exception:
            return False
        same_target = [r for r in rels if r.get("model") == child_model]
        if len(same_target) > 1:
            return True
        # Also detect if any other relation would produce the same last segment as child_endpoint
        # e.g., two different children sharing the same endpoint name
        segments = set()
        for r in rels:
            mdl = r.get("model")
            if mdl is None:
                continue
            inp, outp = get_input_output_from_model_or_make(mdl)
            seg = self._get_url_naming_function(mdl, inp, outp)
            segments.add(seg)
        return list(segments).count(child_endpoint) > 1

    def generate_route(self, **kwargs: dict[str, Any]):
        """Generate the route for this method/model.

        Args:
            **kwargs (Dict[str, Any]): Dictionary of keyword arguments for route generation.
        """
        kwargs["group_tag"] = get_tag_group(kwargs)
        model = kwargs.get("model", kwargs.get("child_model"))
        service = CrudService(model=model, session=kwargs["session"])
        http_method = kwargs.get("method", "GET")

        # Ensure the route is not blocked
        # if self._is_route_blocked(http_method, model):
        #     return

        route_function = create_route_function(
            service,
            http_method,
            many=kwargs.get("many", False),
            join_model=kwargs.get("parent_model"),
            get_field=kwargs.get("join_key"),
            output_schema=kwargs.get("output_schema"),
            plugins=self.architect.plugins,
        )

        unique_route_function = self._create_unique_route_function(
            route_function,
            kwargs["url"],
            http_method,
            kwargs.get("many", False),
            relation_name=kwargs.get("relation_name"),
        )

        if http_method == "GET" and self.architect.cache:
            timeout = self.architect.get_config("API_CACHE_TIMEOUT", 300)
            unique_route_function = self.architect.cache.cached(timeout=timeout)(unique_route_function)

        kwargs["function"] = unique_route_function

        # Register the route with Flask
        self._add_route_to_flask(
            kwargs["url"],
            kwargs["method"],
            self.architect.schema_constructor(**kwargs)(unique_route_function),
        )
        if not kwargs.get("join_key") and not kwargs.get("url_segment"):
            self._add_self_url_function_to_model(model)
        self._add_to_created_routes(**kwargs)

    def _is_route_blocked(self, http_method: str, model: Callable) -> bool:
        """Check if the route is blocked based on the configuration.

        Args:
            http_method (str): The HTTP method of the route.
            model (Callable): The model for the route.

        Returns:
            bool: True if the route is blocked, otherwise False.
        """
        blocked_methods = get_config_or_model_meta("API_BLOCK_METHODS", model=model, default=[], allow_join=True)
        read_only = get_config_or_model_meta("API_READ_ONLY", model=model, default=False)
        if read_only:
            blocked_methods.extend(["POST", "PATCH", "DELETE"])

        return http_method in [x.upper() for x in blocked_methods]

    def _create_unique_route_function(
        self,
        route_function: Callable,
        url: str,
        http_method: str,
        is_many: bool = False,
        *,
        relation_name: str | None = None,
    ) -> Callable:
        """Create a unique route function name.

        Args:
            route_function (Callable): The original route function.
            url (str): The URL of the route.
            http_method (str): The HTTP method of the route.

        Returns:
            Callable: The unique route function.
        """
        # Ensure the function name is unique by differentiating between collection and single item routes
        base = f"route_wrapper_{http_method}_{'collection' if is_many else 'single'}_{url.replace('/', '_')}"
        if relation_name and not base.endswith(f"_{relation_name}"):
            base = f"{base}_{relation_name}"
        unique_function_name = base

        unique_route_function = FunctionType(
            route_function.__code__,
            globals(),
            unique_function_name,
            route_function.__defaults__,
            route_function.__closure__,
        )
        return unique_route_function

    def _add_route_to_flask(self, url: str, method: str, function: Callable):
        """Add a route to Flask.

        Args:
            url (str): The URL endpoint.
            method (str): The HTTP method.
            function (Callable): The function to call when the route is visited.
        """

        logger.log(1, f"|{method}|:`{self.blueprint.url_prefix}{url}` added to flask.")
        self.blueprint.add_url_rule(url, view_func=function, methods=[method])

    def _add_self_url_function_to_model(self, model: Callable, endpoint_segment: str | None = None):
        """Add a self URL method to the model class.

        Args:
            model (Callable): The model to add the function to.
        """
        # Resolve the first primary key attribute name from the mapper; prefer
        # the mapped attribute (e.g., 'id') over the raw DB column name.
        pk_cols = list(sa_inspect(model).primary_key)
        if len(pk_cols) > 1:
            logger.error(
                1,
                f"Composite primary keys are not supported, failed to set method $to_url$ on --{model.__name__}--",
            )
            return

        api_prefix = get_config_or_model_meta("API_PREFIX", default="/api")
        url_naming_function = get_config_or_model_meta("API_ENDPOINT_NAMER", model, default=endpoint_namer)
        segment = endpoint_segment.strip("/") if isinstance(endpoint_segment, str) and endpoint_segment else url_naming_function(model)
        segment = segment.strip("/")

        def to_url(self):
            try:
                mapped_prop = sa_inspect(model).get_property_by_column(pk_cols[0])
                attr_name = getattr(mapped_prop, "key", None)
            except Exception:
                attr_name = None
            if not attr_name:
                attr_name = getattr(pk_cols[0], "key", None) or getattr(pk_cols[0], "name", None)
            return f"{api_prefix}/{segment}/{getattr(self, attr_name)}"

        logger.log(3, f"Adding method $to_url$ to model --{model.__name__}--")
        model.to_url = to_url

    def _add_relation_url_function_to_model(self, id_key: str, child: Callable, parent: Callable, relation_name: str | None = None, relation_url_segment: str | None = None):
        """Add a relation URL method to the model class.

        Args:
            id_key (str): The primary key attribute name.
            child (Callable): The child model.
            parent (Callable): The parent model.
        """
        api_prefix = get_config_or_model_meta("API_PREFIX", default="/api")
        parent_endpoint = get_config_or_model_meta("API_ENDPOINT_NAMER", parent, default=endpoint_namer)(parent)
        child_endpoint = get_config_or_model_meta("API_ENDPOINT_NAMER", child, default=endpoint_namer)(child)
        # Use the same naming resolution as for route building
        naming_mode = self._resolve_relation_route_naming(parent, child)
        # Optional alias map for URL segment
        alias_map = get_config_or_model_meta("RELATION_ROUTE_MAP", model=parent, default={}) or {}
        alias = alias_map.get(relation_name) if relation_name else None
        if relation_url_segment:
            final_segment = relation_url_segment
        elif naming_mode == "relationship" and relation_name:
            final_segment = alias or relation_name
        elif naming_mode == "auto" and relation_name:
            # For auto, we rely on what _prepare_relation_route_data computed; fallback to relationship name
            final_segment = relation_url_segment or alias or relation_name
        else:
            final_segment = child_endpoint

        def to_url(self):
            parent_pk = get_primary_keys(parent).key
            return f"{api_prefix}/{parent_endpoint}/{getattr(self, parent_pk)}/{final_segment}"

        logger.log(
            3,
            f"Adding relation method ${final_segment}_to_url$ to parent model --{parent.__name__}-- linking to --{child.__name__}--.",
        )
        setattr(parent, f"{final_segment.replace('-', '_')}_to_url", to_url)

    def _add_to_created_routes(self, **kwargs: dict[str, Any]):
        """Add a route to the created routes dictionary.

        Args:
            **kwargs (Dict[str, Any]): Dictionary of keyword arguments.
        """
        model = kwargs.get("child_model", kwargs.get("model"))
        route_key = kwargs["name"]

        if self.created_routes is None:
            self.created_routes = {}

        self.created_routes[route_key] = {
            "function": route_key,
            "model": model,
            "name": route_key,
            "method": kwargs["method"],
            "url": kwargs["url"],
            "input_schema": kwargs.get("input_schema"),
            "output_schema": kwargs.get("output_schema"),
        }

    def _get_url_naming_function(self, model: Callable, input_schema: Callable, output_schema: Callable) -> str:
        """Get the URL naming function for a model.

        Args:
            model (Callable): The model to generate the URL for.
            input_schema (Callable): The input schema class.
            output_schema (Callable): The output schema class.

        Returns:
            str: The URL naming string.
        """
        return get_config_or_model_meta("API_ENDPOINT_NAMER", model, default=endpoint_namer)(model, input_schema, output_schema)
