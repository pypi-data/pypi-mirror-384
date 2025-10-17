"""Core application framework with composable apps architecture.

Enterprise-grade framework for Cognite Functions with composable apps,
automatic validation, and built-in introspection capabilities.

This module provides the main FunctionApp class for building type-safe
Cognite Functions. It handles route registration, parameter validation,
automatic type conversion, and error handling. Multiple FunctionApp instances
can be composed together to create modular, reusable functionality.

Key Components:
    - FunctionApp: Main application class with route decorators (@app.get,
      @app.post, etc.)
    - Composable architecture: Multiple apps can be combined using
      create_function_service([app1, app2, app3])
    - Route handling: Automatic parameter extraction from URLs, query
      strings, and request bodies
    - Type safety: Automatic conversion and validation using Pydantic
      models and type hints
    - Error handling: Comprehensive error catching and formatting for
      Cognite Functions
    - Schema generation: OpenAPI-style documentation generation
    - Built-in extensions: MCP integration and introspection endpoints
    - Async support: Application endpoints can be sync or async functions

Example usage:
    ```python
    from cognite_typed_functions import FunctionApp, create_function_service
    from cognite_typed_functions.mcp import create_mcp_app
    from cognite_typed_functions.introspection import create_introspection_app
    from pydantic import BaseModel

    # Main business logic app
    app = FunctionApp("My Function", "1.0.0")

    class ItemResponse(BaseModel):
        id: int
        name: str
        price: float

    @app.get("/items/{item_id}")
    def get_item(client, item_id: int) -> ItemResponse:
        # Function automatically gets typed parameters
        return ItemResponse(id=item_id, name="Widget", price=29.99)

    @app.get("/items/{item_id}/async")
    async def get_item_async(client, item_id: int) -> ItemResponse:
        # Async application endpoints are also supported
        result = await fetch_data_async(item_id)
        return ItemResponse(id=item_id, name=result.name, price=result.price)

    # Create composable extensions
    mcp_app = create_mcp_app("my-server")
    introspection_app = create_introspection_app()

    # Optionally expose routes via MCP
    @mcp_app.tool("Get item by ID")
    @app.get("/items/{item_id}")  # Can decorate the same function
    def get_item_mcp(client, item_id: int) -> ItemResponse:
        return get_item(client, item_id)

    # Compose all apps together (introspection first to see all apps)
    handle = create_function_service(introspection_app, mcp_app, app)
    ```

The framework supports:
- Path parameters: /items/{item_id}
- Query parameters: ?include_tax=true&category=electronics
- Request body parsing and validation
- Automatic type conversion based on function signatures
- Input/output model validation with Pydantic
- Composable apps architecture for modular functionality
- MCP (Model Context Protocol) integration
- Built-in introspection endpoints (/__health__, /__schema__, etc.)
- Pattern-based routing for advanced use cases
- Comprehensive error handling with structured responses
- Both sync and async application endpoints
"""

import asyncio
import inspect
from collections.abc import Callable, Coroutine, Mapping, Sequence
from functools import wraps
from typing import (
    Any,
    ParamSpec,
    TypeVar,
    cast,
    get_type_hints,
)

from cognite.client import CogniteClient
from pydantic import BaseModel, ValidationError

from ._version import __version__
from .convert import ConvertError, convert_arguments_to_typed_params
from .dependency_registry import DependencyRegistry, create_default_registry, resolve_dependencies
from .models import (
    CogniteTypedError,
    CogniteTypedResponse,
    ConfigurationError,
    DataDict,
    FunctionCallInfo,
    FunctionService,
    HTTPMethod,
    RequestData,
    SecretsMapping,
    TypedResponse,
)
from .routing import PathParams, RouteInfo, Router

_P = ParamSpec("_P")  # , bound=RequestHandler, wait for Python 3.13)
_R = TypeVar("_R")


class FunctionApp:
    """Composable application for building Cognite Function services."""

    def __init__(
        self,
        title: str = "Cognite Typed Functions",
        version: str = __version__,
        registry: DependencyRegistry | None = None,
    ):
        """Initialize the FunctionApp.

        Args:
            title: The title of the app.
            version: The version of the app.
            registry: Optional dependency registry for custom dependencies.
                      Custom providers take priority over defaults, allowing overrides
                      (e.g., mock client for testing). Defaults are used as fallback.
        """
        self.title = title
        self.version = version

        # Custom providers should be prioritized over defaults to allow overrides
        if registry:
            # Create new registry with custom providers first, then defaults as fallback
            self.registry = DependencyRegistry()
            self.registry.update(registry)  # Custom providers (higher priority)
            self.registry.update(create_default_registry())  # Default providers (fallback)
        else:
            self.registry = create_default_registry()

        self.router = Router()

    def set_context(
        self,
        routes: Mapping[str, Mapping[HTTPMethod, RouteInfo]],
        apps: Sequence["FunctionApp"],
        shared_registry: DependencyRegistry | None = None,
    ) -> None:
        """Set the composition context for this app.

        This method is called automatically during app composition and can be
        overridden by apps that need access to routes and apps from the entire composition.

        Args:
            routes: Routes from apps with lower priority (to the right in composition order)
            apps: Apps with lower priority (to the right in composition order)
            shared_registry: Optional shared dependency registry from the main app
        """
        # Default implementation does nothing - apps can override as needed
        pass

    def extract_path_params(self, path: str) -> Sequence[str]:
        """Extract parameter names from path like /items/{item_id}."""
        return self.router.extract_path_params(path)

    def register_route(
        self,
        path: str,
        method: HTTPMethod,
        # We use Callable[..., Any] to support both sync and async application endpoints
        # The actual validation happens at runtime in execute_function_and_format_response
        func: Callable[..., Any],
        description: str = "",
    ) -> None:
        """Register a route with the app.

        Supports both sync and async application endpoints.
        """
        # Extract function signature for parameter inspection
        sig = inspect.signature(func)
        try:
            type_hints = get_type_hints(func)
        except (NameError, AttributeError):
            # Fallback for functions with type hints that can't be resolved
            # (e.g., adapter functions with JSONLike references)
            type_hints = {}

        # Skip dependency injection parameters
        # These are framework-provided and not part of the user's request parameters
        dependency_param_names = self.registry.get_dependency_param_names(sig)
        params = {name: param for name, param in sig.parameters.items() if name not in dependency_param_names}

        # Check for collisions between path parameters and dependencies
        path_param_names = self.extract_path_params(path)
        dependency_path_params = list(set(path_param_names) & dependency_param_names)
        if dependency_path_params:
            raise ConfigurationError(
                f"Route '{path}' has path parameters {dependency_path_params} "
                "that conflict with registered dependencies. "
                "Rename either the path parameter(s) or the dependency/dependencies."
            )

        route_info = RouteInfo(
            method=method,
            endpoint=func,
            signature=sig,
            parameters=params,
            type_hints=type_hints,
            path_params=self.extract_path_params(path),
            description=description or func.__doc__ or f"{method} {path}",
        )

        self.router.register_route(path, method, route_info)

    @property
    def routes(self) -> Mapping[str, Mapping[HTTPMethod, RouteInfo]]:
        """Get all routes registered with the app."""
        return self.router.routes

    async def dispatch_request(
        self,
        request: RequestData,
        client: CogniteClient,
        secrets: SecretsMapping | None = None,
        function_call_info: FunctionCallInfo | None = None,
    ) -> DataDict | None:
        """Dispatch a request and return the response.

        This method enables flexible inter-app communication by allowing
        one app to dispatch requests to another app or to itself.

        Args:
            request: The request data containing path, method, body, and query parameters
            client: The Cognite client instance
            secrets: Optional secrets mapping (injected if the application endpoint declares it)
            function_call_info: Optional function call metadata (injected if the application endpoint declares it)

        Returns:
            Response data dict if a route matches, None if no route matches

        Raises:
            ValidationError: If input validation fails
            ConvertError: If parameter conversion fails
            Exception: If function execution fails
        """
        # Find matching route and extract path parameters
        route_match, path_params = self.router.find_matching_route(request.clean_path, request.method)

        if not route_match:
            # No route matched
            return None

        # Prepare function arguments with validation and type coercion
        kwargs = self._prepare_function_arguments(
            client,
            route_match,
            request.body,
            request.query,
            path_params,
            secrets,
            function_call_info,
        )

        # Execute function and format response
        return await execute_function_and_format_response(route_match, kwargs)

    def _prepare_function_arguments(
        self,
        client: CogniteClient,
        route_match: RouteInfo,
        body: DataDict,
        query: Mapping[str, str | Sequence[str]],
        path_params: PathParams,
        secrets: SecretsMapping | None = None,
        function_call_info: FunctionCallInfo | None = None,
    ) -> dict[str, object]:
        """Prepare and validate function arguments with type coercion and dependency injection.

        Uses cached signature and type hints from RouteInfo to avoid repeated introspection.
        """
        # Combine body, query, and path parameters
        all_params = {**body, **query, **path_params}

        func = route_match.endpoint

        # Resolve dependencies using the cached signature
        dependencies = resolve_dependencies(
            func,
            client,
            secrets,
            function_call_info,
            self.registry,
            signature=route_match.signature,
        )

        # Convert user-provided arguments to typed parameters using cached signature and type hints
        converted_params = convert_arguments_to_typed_params(
            all_params,
            dependency_names=self.registry.get_dependency_param_names(route_match.signature),
            signature=route_match.signature,
            type_hints=route_match.type_hints,
        )

        # Merge dependencies and converted parameters
        return {**dependencies, **converted_params}

    def _create_route_decorator(
        self,
        method: HTTPMethod,
        path: str,
    ) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
        """Create a route decorator for the specified HTTP method.

        Supports both sync and async application endpoints.
        """

        def decorator(
            func: Callable[_P, _R],
        ) -> Callable[_P, _R]:
            self.register_route(path, method, func)
            return func

        return decorator

    def get(
        self,
        path: str,
    ) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
        """Decorator for GET operations (data retrieval).

        Supports both sync and async endpoints.
        """
        return self._create_route_decorator(HTTPMethod.GET, path)

    def post(
        self,
        path: str,
    ) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
        """Decorator for POST operations (create/process).

        Supports both sync and async endpoints.
        """
        return self._create_route_decorator(HTTPMethod.POST, path)

    def put(
        self,
        path: str,
    ) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
        """Decorator for PUT operations (update/replace).

        Supports both sync and async endpoints.
        """
        return self._create_route_decorator(HTTPMethod.PUT, path)

    def delete(
        self,
        path: str,
    ) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
        """Decorator for DELETE operations.

        Supports both sync and async endpoints.
        """
        return self._create_route_decorator(HTTPMethod.DELETE, path)


async def call_endpoint(func: Callable[..., _R], **kwargs: Any) -> _R:
    """Call the endpoint decorated function, automatically handling both sync and async functions.

    Calls the application endpoint function, automatically handling both
    sync and async functions. Async functions are awaited directly,
    while sync functions are run on a thread pool to avoid blocking the
    event loop.

    Args:
        func: The application endpoint function to call (sync or async)
        **kwargs: Arguments to pass to the endpoint function

    Returns:
        The result from the function
    """
    if inspect.iscoroutinefunction(func):
        # Async endpoint - await it directly
        return await func(**kwargs)
    else:
        # Sync endpoint - run on thread pool to avoid blocking
        return await asyncio.to_thread(func, **kwargs)


def cognite_error_handler(
    func: Callable[_P, Coroutine[Any, Any, DataDict]],
) -> Callable[_P, Coroutine[Any, Any, DataDict]]:
    """Decorator that handles common errors in async application endpoints.

    This decorator works with async functions and returns error dicts instead
    of raising exceptions. Both sync and async callers benefit from this
    centralized error handling.
    """

    @wraps(func)
    async def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> DataDict:
        try:
            return await func(*args, **kwargs)
        except ValidationError as e:
            # Handle validation errors from Pydantic on the returned data
            return CogniteTypedError(
                error_type="ValidationError",
                message=f"Input validation failed: {e.error_count()} error(s)",
                details={"errors": e.errors()},
            ).model_dump()
        except ConvertError as e:
            # Handle parameter conversion and validation errors on input data
            return CogniteTypedError(
                error_type="ValidationError",
                message=f"Input validation failed: {e!s}",
                details={"exception_type": type(e).__name__},
            ).model_dump()
        except Exception as e:
            return CogniteTypedError(
                error_type="ExecutionError",
                message=f"Function execution failed: {e!s}",
                details={"exception_type": type(e).__name__},
            ).model_dump()

    return wrapper


async def execute_function_and_format_response(
    route_match: RouteInfo,
    kwargs: Mapping[str, Any],  # This must be Any
) -> DataDict:
    """Execute the function and format the response.

    Supports both sync and async endpoints via the call_endpoint helper.
    """
    func = route_match.endpoint
    result = await call_endpoint(func, **kwargs)

    # Handle result conversion based on type
    data = result.model_dump() if isinstance(result, BaseModel) else result

    return CogniteTypedResponse(data=cast(TypedResponse, data)).model_dump()


def create_function_service(*apps: FunctionApp) -> FunctionService:
    """Create function service from single app or composed apps (left-to-right evaluation).

    Args:
        apps: Single FunctionApp or sequence of FunctionApp to compose.
              For composed apps, endpoint routing tries each app
              left-to-right until one matches.

    Returns:
        FunctionService handle instance compatible with Cognite Functions. May also be
        used asyncrhonously with the devserver.

    Example:
        # Single app
        handle = create_function_service(main_app)

        # Composed apps (Introspection first to see all, then MCP, then Main)
        handle = create_function_service(introspection_app, mcp_app, main_app)
    """
    # Normalize to list
    app_list = list(apps)

    # Provide composition context to apps that implement CompositionAware
    _set_app_context(app_list)

    @cognite_error_handler
    async def _async_handle(
        *,
        client: CogniteClient,
        data: DataDict,
        secrets: SecretsMapping | None = None,
        function_call_info: FunctionCallInfo | None = None,
    ) -> DataDict:
        """Async implementation of the handle entry point.

        Expected data format:
        {
            "path": "/items/123?include_tax=true&q=search",  # Full URL with query string
            "method": "GET",
            "body": {...}  # Optional request body for POST/PUT operations
        }
        """
        # Parse request data using Pydantic (we need the cast here since Pydantic is doing the validation)
        request = RequestData(**cast(dict[str, Any], data))

        # Try each app in order (left-to-right evaluation)
        for app in app_list:
            # Dispatch request to app and get response if route matches
            response = await app.dispatch_request(request, client, secrets, function_call_info)

            if response is not None:
                return response

        # No app matched the route
        all_routes: list[str] = []
        for app in app_list:
            all_routes.extend(app.router.routes.keys())

        return CogniteTypedError(
            error_type="RouteNotFound",
            message=f"No route found for {request.method} {request.clean_path}",
            details={"available_routes": all_routes},
        ).model_dump()

    def handle(
        *,
        client: CogniteClient,
        data: DataDict,
        secrets: SecretsMapping | None = None,
        function_call_info: FunctionCallInfo | None = None,
    ) -> DataDict:
        """Sync wrapper for cross-cloud compatibility (AWS, GCP, Azure).

        This sync wrapper allows the handler to work across all cloud platforms
        while internally using async for efficient execution of both sync and async handlers.

        Error handling is performed in _async_handle, so this wrapper just propagates
        the result (either success or error dict).
        """
        return asyncio.run(
            _async_handle(
                client=client,
                data=data,
                secrets=secrets,
                function_call_info=function_call_info,
            )
        )

    # Return FunctionService with both sync and async handles
    return FunctionService(sync_handle=handle, async_handle=_async_handle)


def _set_app_context(app_list: list[FunctionApp]) -> None:
    """Provide composition context to all apps in the composition.

    Following layered architecture principles, each app only sees downstream apps
    (lower priority apps to their right). If an app needs global visibility,
    put it first in the composition order.

    The registry from the main app (last in the list) is shared with all apps,
    allowing them to use the same dependency injection configuration.
    """
    # Use the main app's registry (last app in the list, typically the business logic)
    shared_registry = app_list[-1].registry if app_list else None

    # Provide context to each app based on its position
    for i, app in enumerate(app_list):
        # Collect downstream apps and routes (lower priority, to the right)
        downstream_apps = app_list[i + 1 :]
        downstream_routes: dict[str, dict[HTTPMethod, RouteInfo]] = {}
        for downstream_app in reversed(downstream_apps):
            for path, methods in downstream_app.routes.items():
                downstream_routes.setdefault(path, {}).update(methods)
        # Provide downstream visibility and shared registry to the app
        app.set_context(downstream_routes, downstream_apps, shared_registry)
