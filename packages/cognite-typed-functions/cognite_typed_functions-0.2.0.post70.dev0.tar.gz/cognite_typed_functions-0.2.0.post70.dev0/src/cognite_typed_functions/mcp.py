"""Model Context Protocol (MCP) integration as a composable app.

This module provides MCP (Model Context Protocol) support as a separate FunctionApp
that can be composed with other apps. The MCP app handles /__mcp_* routes and
mirrors routes from the main app using the @mcp_app.tool() decorator.

Key Features:
    - Clean separation: MCP is its own FunctionApp using standard decorators
    - Route mirroring: @mcp_app.tool() creates MCP-specific tool endpoints
    - No forwarding complexity: MCP app has its own application endpoints
    - Standard composition: Works with create_function_service(mcp_app, app)

Example Usage:
    ```python
    from cognite_typed_functions import FunctionApp, create_function_service
    from cognite_typed_functions.mcp import create_mcp_app

    # Create apps
    mcp_app = create_mcp_app()
    app = FunctionApp("My API", "1.0.0")

    # Use tool decorator to mirror routes
    @app.get("/items/{item_id}")
    @mcp_app.tool(description="Get item by ID")
    def get_item(client: CogniteClient, item_id: int) -> ItemResponse:
        return ItemResponse(id=item_id, name="Widget")

    # Compose apps (MCP first to handle /__mcp_* routes)
    handle = create_function_service(mcp_app, app)
    ```

Architecture:
    1. MCP app handles /__mcp_tools__ (lists available tools)
    2. MCP app handles /__mcp_call__/{tool_name} (executes tools)
    3. @mcp_app.tool() decorator creates mirrored application endpoints in MCP app
    4. Main app handles regular business logic routes
    5. Request routing: MCP → Introspection → Main (first match wins)
"""

import inspect
import warnings
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, ParamSpec, TypeVar, cast, get_args, get_origin, get_type_hints

from cognite.client import CogniteClient
from pydantic import BaseModel, ValidationError

from ._version import __version__
from .app import FunctionApp, call_endpoint
from .convert import ConvertError, convert_arguments_to_typed_params
from .dependency_registry import DependencyRegistry, resolve_dependencies
from .models import CogniteTypedError, DataDict, FunctionCallInfo, Json, SecretsMapping, TypedResponse

_P = ParamSpec("_P")
_R = TypeVar("_R")


@dataclass
class MCPTool:
    """MCP Tool definition with metadata and tool endpoint.

    The tool endpoint can be either sync or async.
    Schema is generated lazily to account for registry updates during composition.
    """

    name: str
    description: str
    tool_endpoint: Callable[..., Any]  # Can be sync or async
    _func: Callable[..., Any]  # Original function for lazy schema generation
    _registry_provider: Callable[[], DependencyRegistry]  # Lazy provider for dependency registry

    @property
    def input_schema(self) -> DataDict:
        """Generate input schema lazily using current dependency registry."""
        return _generate_input_schema(self._func, self._registry_provider())


class MCPApp(FunctionApp):
    """MCP-specific subclass of FunctionApp with typed attributes."""

    def __init__(self, server_name: str = "cognite-functions", title: str | None = None, version: str = __version__):
        """Initialize the MCPApp.

        Args:
            server_name: Name of the MCP server
            title: The title of the app (defaults to MCP-{server_name})
            version: The version of the app
        """
        super().__init__(title or f"MCP-{server_name}", version)
        self._server_name = server_name
        self._tools: dict[str, MCPTool] = {}

    @property
    def server_name(self) -> str:
        """Get the MCP server name."""
        return self._server_name

    @property
    def tools(self) -> list[MCPTool]:
        """Get the list of registered MCP tools."""
        return list(self._tools.values())

    def get_tool(self, name: str) -> MCPTool | None:
        """Get a tool by name.

        Args:
            name: The name of the tool to retrieve

        Returns:
            The tool if found, None otherwise
        """
        return self._tools.get(name)

    def get_tool_names(self) -> list[str]:
        """Get list of registered tool names.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    def tool(self, description: str = "") -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
        """Decorator to register a function as an MCP tool.

        This creates a mirrored application endpoint in the MCP app that can be called
        via /__mcp_call__/{tool_name}.

        Supports both sync and async functions.

        Args:
            description: Description of the tool for MCP clients. If not
            provided, a description derived from the function docstring.

        Returns:
            Decorator that registers the function as an MCP tool
        """

        def decorator(func: Callable[_P, _R]) -> Callable[_P, _R]:
            # Generate tool name and description
            tool_name = _generate_tool_name(func)
            tool_description = description or _extract_description(func)

            # Cast the function to a callable since ParamSpec cannot be bound to a RouteEndpoint 🙈
            _func = cast(Callable[..., Any], func)

            # Pre-compute signature and type hints for efficient reuse
            _sig = inspect.signature(_func)
            _type_hints = get_type_hints(_func)

            # Create mirrored application endpoint that transforms MCP request to function call
            async def mcp_tool_endpoint(
                client: CogniteClient,
                secrets: SecretsMapping | None = None,
                function_call_info: FunctionCallInfo | None = None,
                **kwargs: DataDict,
            ) -> _R:
                """Mirrored route endpoint that executes the original function (sync or async)."""
                # Resolve dependencies using the standard helper with pre-computed signature
                dependencies = resolve_dependencies(
                    _func, client, secrets, function_call_info, self.registry, signature=_sig
                )

                # Convert MCP arguments to typed parameters with pre-computed signature and type hints
                converted_params = convert_arguments_to_typed_params(
                    kwargs,
                    dependency_names=self.registry.get_dependency_param_names(_sig) if self.registry else frozenset(),
                    signature=_sig,
                    type_hints=_type_hints,
                )

                # Merge dependencies and converted parameters
                typed_kwargs = {**dependencies, **converted_params}

                # Call original function using the call_endpoint helper
                return await call_endpoint(_func, **typed_kwargs)

            # Register the tool with lazy schema generation
            # The registry provider is a function that reads from self.registry
            # This ensures the schema uses the current registry state (after composition)
            def get_registry() -> DependencyRegistry:
                assert self.registry is not None  # Set during composition
                return self.registry

            tool = MCPTool(
                name=tool_name,
                description=tool_description,
                tool_endpoint=mcp_tool_endpoint,
                _func=_func,
                _registry_provider=get_registry,
            )

            # Warn if overwriting an existing tool
            if tool_name in self._tools:
                warnings.warn(
                    f"Tool '{tool_name}' is being overwritten. Previous tool with the same name will be replaced.",
                    UserWarning,
                    stacklevel=2,
                )

            self._tools[tool_name] = tool

            # Return original function unchanged
            return func

        return decorator


def create_mcp_app(server_name: str = "cognite-functions") -> MCPApp:
    """Create an MCP app that handles /__mcp_* routes.

    Args:
        server_name: Name of the MCP server

    Returns:
        MCPApp configured with MCP endpoints and tool decorator
    """
    mcp_app = MCPApp(server_name=server_name)

    @mcp_app.get("/__mcp_tools__")
    def get_mcp_tools(client: CogniteClient) -> dict[str, Any]:
        """Get list of available MCP tools."""
        tool_list: list[dict[str, Any]] = []
        for tool in mcp_app.tools:
            tool_list.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": {
                        "type": "object",
                        "properties": tool.input_schema.get("properties", {}),
                        "required": tool.input_schema.get("required", []),
                    },
                }
            )

        return {"tools": tool_list, "_meta": {"server": mcp_app.server_name, "total_tools": len(tool_list)}}

    @mcp_app.post("/__mcp_call__/{tool_name}")
    async def handle_mcp_call(
        client: CogniteClient,
        secrets: SecretsMapping | None,
        function_call_info: FunctionCallInfo | None,
        tool_name: str,
        **kwargs: Any,
    ) -> DataDict:
        """Execute an MCP tool call.

        Supports forwarding to both sync and async application endpoints.
        """
        # Find the tool using O(1) dictionary lookup
        tool = mcp_app.get_tool(tool_name)
        if not tool:
            available_tools = mcp_app.get_tool_names()
            return _create_mcp_error(
                "MCPToolNotFound", f"Tool '{tool_name}' not found", {"available_tools": available_tools}
            )

        try:
            # Execute the mirrored tool application endpoint with dependency injection
            result = await call_endpoint(
                tool.tool_endpoint, client=client, secrets=secrets, function_call_info=function_call_info, **kwargs
            )

            # Format result for MCP
            return _format_mcp_response(result, tool_name)

        except (ValidationError, ConvertError) as e:
            return _create_mcp_error(
                "MCPValidationError",
                f"Tool input validation failed: {e!s}",
                {"tool_name": tool_name, "exception_type": type(e).__name__},
            )
        except Exception as e:
            return _create_mcp_error(
                "MCPExecutionError",
                f"Tool execution failed: {e!s}",
                {"tool_name": tool_name, "exception_type": type(e).__name__},
            )

    return mcp_app


def _generate_tool_name(func: Callable[..., Any]) -> str:
    """Generate a tool name from function name and route info."""
    # For now, use the application endpoint function name directly
    # Later we could incorporate route path/method if needed
    return func.__name__


def _extract_description(func: Callable[..., Any]) -> str:
    """Extract description from function docstring."""
    doc = inspect.getdoc(func)
    if doc:
        return doc
    return f"MCP tool for {func.__name__}"


def _generate_input_schema(func: Callable[..., Any], registry: DependencyRegistry) -> DataDict:
    """Generate JSON schema for function parameters.

    Args:
        func: Function to generate schema for
        registry: Dependency registry to check which parameters are dependencies

    Returns:
        JSON schema dictionary for the function's parameters
    """
    try:
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)

        # Skip dependency injection parameters
        dependency_param_names = registry.get_dependency_param_names(sig)
        params = {name: param for name, param in sig.parameters.items() if name not in dependency_param_names}

        properties: DataDict = {}
        required: list[str] = []

        for param_name, param in params.items():
            # Basic type mapping
            param_type: type[Any] = type_hints.get(param_name, str)
            schema_type = _python_type_to_json_schema(param_type)

            properties[param_name] = schema_type

            # Check if required (no default value)
            if param.default is inspect.Parameter.empty:
                required.append(param_name)

        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }

    except (TypeError, NameError) as e:
        # Type hint resolution errors (forward references, missing imports, etc.)
        warnings.warn(
            f"Failed to resolve type hints for function {func.__name__}: {e}. Using empty schema.",
            UserWarning,
            stacklevel=2,
        )
        return {"type": "object", "properties": {}, "required": []}
    except ValueError as e:
        # Signature inspection errors (malformed signatures, etc.)
        warnings.warn(
            f"Failed to inspect signature for function {func.__name__}: {e}. Using empty schema.",
            UserWarning,
            stacklevel=2,
        )
        return {"type": "object", "properties": {}, "required": []}
    except Exception as e:
        # Unexpected errors - these should be investigated
        warnings.warn(
            f"Unexpected error generating schema for function {func.__name__}: {e}. Using empty schema.",
            RuntimeWarning,
            stacklevel=2,
        )
        return {"type": "object", "properties": {}, "required": []}


def _python_type_to_json_schema(python_type: type[Any]) -> DataDict:
    """Convert Python type to JSON schema type."""
    origin = get_origin(python_type)
    args = get_args(python_type)

    # Handle basic types
    match python_type:
        case x if x is str:
            return {"type": "string"}
        case x if x is int:
            return {"type": "integer"}
        case x if x is float:
            return {"type": "number"}
        case x if x is bool:
            return {"type": "boolean"}
        case x if x is list:
            # Raw list, items can be anything
            return {"type": "array", "items": {}}
        case x if x is dict:
            return {"type": "object"}
        case _:
            # Continue to generic type handling
            pass
    if inspect.isclass(python_type) and issubclass(python_type, BaseModel):
        schema = python_type.model_json_schema()
        # The title is not needed for a parameter schema.
        schema.pop("title", None)
        return schema

    if origin is list:
        # list[T]
        return {"type": "array", "items": _python_type_to_json_schema(args[0]) if args else {}}
    if origin is dict:
        # dict[K, V]
        if args and len(args) == 2:
            # JSON object keys must be strings. We assume that and schema the values.
            return {"type": "object", "additionalProperties": _python_type_to_json_schema(args[1])}
        return {"type": "object"}

    # Default to object for other complex types
    return {"type": "object"}


def _create_mcp_error(error_type: str, message: str, details: DataDict) -> DataDict:
    """Create standardized MCP error response."""
    return CogniteTypedError(error_type=error_type, message=message, details=details).model_dump()


def _typed_response_to_json(value: TypedResponse) -> Json:
    """Recursively convert TypedResponse to Json by converting all BaseModel instances."""
    match value:
        case BaseModel():
            return value.model_dump()
        case dict():
            return {k: _typed_response_to_json(v) for k, v in value.items()}
        case list():
            return [_typed_response_to_json(item) for item in value]
        case _:
            # Primitives pass through
            return cast(Json, value)


def _format_mcp_response(result: TypedResponse, tool_name: str) -> DataDict:
    """Format function result for MCP response."""
    # Convert result to JSON-compatible structure
    json_result = _typed_response_to_json(result)

    # Wrap primitives in a result field
    match json_result:
        case dict():
            data: DataDict = json_result
        case _:
            data = {"result": json_result}

    return {"success": True, "tool_name": tool_name, "data": data, "_meta": {"result_type": type(result).__name__}}
