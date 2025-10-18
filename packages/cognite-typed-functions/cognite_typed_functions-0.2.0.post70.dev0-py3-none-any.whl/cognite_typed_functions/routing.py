"""Route matching and management for Cognite Functions.

This module contains all routing logic, separated from the main FunctionApp
to follow the Single Responsibility Principle. The Router class handles:
- Route storage and sorting
- Path parameter extraction and matching
- Route lookup and selection

This separation makes the code more testable, reusable, and maintainable.
"""

import inspect
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, NewType, TypeAlias

from .models import HTTPMethod, TypedResponse

# Type aliases for routing
PathParams: TypeAlias = Mapping[str, str]


@dataclass
class RouteInfo:
    """Information about a registered route in FunctionApp."""

    method: HTTPMethod
    """HTTPMethod value"""
    endpoint: Callable[..., TypedResponse]
    """The actual callable decorated application endpoint for this route"""

    signature: inspect.Signature
    """Function's signature obtained from inspect.signature()"""
    parameters: Mapping[str, inspect.Parameter]
    """Parameter names mapped to Parameter objects"""
    type_hints: Mapping[str, Any]
    """Type annotations for the function parameters"""
    path_params: Sequence[str]
    """List of path parameter names extracted from the route pattern"""
    description: str
    """Human-readable description of what this route does"""


# NewType for type-safe sorted routes - ensures find_matching_route only accepts properly sorted routes
SortedRoutes = NewType("SortedRoutes", Sequence[tuple[str, Mapping[HTTPMethod, RouteInfo]]])


class Router:
    """Route management system for HTTP-style path matching and parameter extraction.

    The Router class handles all routing logic for Cognite Functions, including:
    - Route storage and organization
    - Intelligent route sorting (exact paths before parameterized)
    - Path parameter extraction from URLs like /items/{item_id}
    - Route matching with type-safe results

    ## Architecture

    Extracted from FunctionApp to follow the Single Responsibility Principle.
    While FunctionApp provides the high-level decorator API (@app.get, @app.post),
    Router focuses purely on the mechanics of routing.

    ## Key Features

    - **Type Safety**: Uses SortedRoutes NewType to prevent misuse
    - **Smart Sorting**: Exact paths like '/items/special' match before '/items/{id}'
    - **Parameter Extraction**: Automatically extracts {param} values from URLs
    - **Reusability**: Can be used standalone or embedded in other frameworks
    - **Testability**: Clean, focused API makes testing straightforward

    ## Usage

    ### Basic Usage
    ```python
    router = Router()

    # Register a route
    route_info = RouteInfo(...)
    router.register_route("/items/{item_id}", HTTPMethod.GET, route_info)

    # Find matching routes
    route, params = router.find_matching_route("/items/123", "GET")
    # Returns: (RouteInfo, {"item_id": "123"})
    ```

    ### Route Matching Priority
    ```python
    router.register_route("/items/special", HTTPMethod.GET, exact_route)
    router.register_route("/items/{item_id}", HTTPMethod.GET, param_route)

    # Exact matches take priority
    route, params = router.find_matching_route("/items/special", "GET")
    # Returns: (exact_route, {})

    route, params = router.find_matching_route("/items/123", "GET")
    # Returns: (param_route, {"item_id": "123"})
    ```

    ### Multiple Routers (Advanced)
    ```python
    api_v1_router = Router()
    api_v2_router = Router()

    # Each router maintains independent route tables
    # Useful for API versioning or modular applications
    ```

    ## Implementation Notes

    - Routes are sorted on-demand via the `sorted_routes` property
    - Sorting algorithm: exact paths (priority 0) before parameterized (priority 1)
    - Secondary sort by path string for deterministic ordering
    - Path parameters are extracted using regex matching
    - Type-safe SortedRoutes prevent accidentally passing unsorted route data
    """

    def __init__(self) -> None:
        """Initialize an empty router."""
        self.routes: dict[str, dict[HTTPMethod, RouteInfo]] = {}

    def register_route(self, path: str, method: HTTPMethod, route_info: RouteInfo) -> None:
        """Register a route with the router.

        Args:
            path: The route path pattern (e.g., "/items/{item_id}")
            method: The HTTP method
            route_info: Complete route information including application endpoint, parameters, etc.
        """
        if path not in self.routes:
            self.routes[path] = {}
        self.routes[path][method] = route_info

    @property
    def sorted_routes(self) -> SortedRoutes:
        """Get routes sorted for efficient matching (exact paths before parameterized paths).

        Exact paths like '/items/special' are matched before parameterized paths like '/items/{item_id}'.
        This ensures that more specific routes take precedence over generic ones.

        Returns:
            SortedRoutes: Type-safe sorted routes that can only be created through this property
        """
        return SortedRoutes(sorted(self.routes.items(), key=self._route_sort_key))

    @staticmethod
    def _route_sort_key(route_item: tuple[str, dict[HTTPMethod, RouteInfo]]) -> tuple[int, str]:
        """Sort key for route prioritization.

        Returns:
            Tuple of (priority, path) where:
            - priority: 0 for exact paths, 1 for parameterized paths
            - path: the route path for deterministic secondary sorting
        """
        path, _ = route_item
        # Exact paths (priority 0) come before parameterized paths (priority 1)
        priority = 1 if "{" in path else 0
        return (priority, path)

    @staticmethod
    def extract_path_params(path: str) -> Sequence[str]:
        """Extract parameter names from path like /items/{item_id}."""
        return re.findall(r"\{(\w+)\}", path)

    def find_matching_route(self, path: str, method: HTTPMethod) -> tuple[RouteInfo | None, PathParams]:
        """Find matching route and extract path parameters.

        Args:
            path: The target path to match against
            method: The HTTP method to match

        Returns:
            Tuple of (matched RouteInfo, extracted path parameters) or (None, {}) if no match
        """
        return find_matching_route(self.sorted_routes, path, method)


def _build_route_pattern(route_path: str, param_names: Sequence[str]) -> str:
    """Convert route path with {param} to regex pattern."""
    pattern = route_path
    for param in param_names:
        pattern = pattern.replace(f"{{{param}}}", r"([^/]+)")
    return f"^{pattern}$"


def _extract_path_parameters(match: re.Match[str], param_names: Sequence[str]) -> PathParams:
    """Extract path parameter values from regex match."""
    return {param: match.group(i + 1) for i, param in enumerate(param_names)}


def _match_path_with_parameters(route_path: str, target_path: str, param_names: Sequence[str]) -> PathParams | None:
    """Handle path parameter matching for a route with known parameters."""
    pattern = _build_route_pattern(route_path, param_names)
    match = re.match(pattern, target_path)
    if match:
        return _extract_path_parameters(match, param_names)
    return None


def _check_path_match(route_path: str, target_path: str, param_names: Sequence[str]) -> PathParams | None:
    """Check if target path matches route path and extract parameters."""
    # Exact path matches: /items, /health, /users
    if route_path == target_path:
        return {}

    # Handle path parameters: /items/{item_id}, /users/{user_id}/orders
    if param_names:
        return _match_path_with_parameters(route_path, target_path, param_names)

    return None


def find_matching_route(
    sorted_routes: SortedRoutes, path: str, method: HTTPMethod
) -> tuple[RouteInfo | None, PathParams]:
    """Find matching route and extract path parameters.

    Args:
        sorted_routes: Type-safe sorted routes from Router.sorted_routes property
        path: The target path to match against
        method: The HTTP method to match

    Returns:
        Tuple of (matched RouteInfo, extracted path parameters) or (None, {}) if no match
    """
    for route_path, methods in sorted_routes:
        if method in methods:
            route_info = methods[method]
            extracted_params = _check_path_match(route_path, path, route_info.path_params)
            if extracted_params is not None:
                return route_info, extracted_params
    return None, {}
