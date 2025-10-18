"""Unit tests for Router class and standalone routing functions.

Tests route registration, path matching, parameter extraction, and route
sorting independently of the full FunctionApp context for better isolation.
"""

import inspect
from collections.abc import Mapping

from cognite.client import CogniteClient

from cognite_typed_functions.models import FunctionCallInfo, HTTPMethod, SecretsMapping
from cognite_typed_functions.routing import (
    RouteInfo,
    Router,
    SortedRoutes,
    find_matching_route,
)

from .conftest import TestItem as Item
from .conftest import TestItemResponse as ItemResponse


class TestRouter:
    """Tests for Router class functionality including registration, sorting, and matching."""

    def test_router_route_registration(self):
        """Test that the Router can register routes and store them correctly."""
        router = Router()

        # Create a simple route handler
        def get_item(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> ItemResponse:
            item_id = params.get("item_id", 1)
            if not isinstance(item_id, int):
                item_id = 1
            item = Item(name=f"Item {item_id}", price=100.0)
            return ItemResponse(id=item_id, item=item, total_price=100.0)

        # Create route info with handler metadata
        route_info = RouteInfo(
            method=HTTPMethod.GET,
            endpoint=get_item,
            signature=inspect.signature(get_item),
            parameters={
                name: param for name, param in inspect.signature(get_item).parameters.items() if name != "client"
            },
            type_hints={},
            path_params=["item_id"],
            description="Get an item by ID",
        )

        # Register the route
        router.register_route("/items/{item_id}", HTTPMethod.GET, route_info)

        # Verify registration
        assert "/items/{item_id}" in router.routes
        assert HTTPMethod.GET.value in router.routes["/items/{item_id}"]
        assert router.routes["/items/{item_id}"][HTTPMethod.GET] == route_info

    def test_router_sorting_behavior_directly(self):
        """Test that routes are sorted with exact paths before parameterized paths, alphabetically within each group."""
        router = Router()

        def dummy_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> Mapping[str, str]:
            return {"status": "ok"}

        # Create minimal route info for testing sorting
        def create_route_info(path_params: list[str]) -> RouteInfo:
            return RouteInfo(
                method=HTTPMethod.GET,
                endpoint=dummy_handler,
                signature=inspect.signature(dummy_handler),
                parameters={},
                type_hints={},
                path_params=path_params,
                description="Test route",
            )

        # Register routes in mixed order to test sorting
        router.register_route("/users/{user_id}", HTTPMethod.GET, create_route_info(["user_id"]))  # param
        router.register_route("/health", HTTPMethod.GET, create_route_info([]))  # exact
        router.register_route("/items/{item_id}", HTTPMethod.GET, create_route_info(["item_id"]))  # param
        router.register_route("/status", HTTPMethod.GET, create_route_info([]))  # exact

        # Get sorted routes
        sorted_routes = router.sorted_routes
        route_paths = [path for path, _ in sorted_routes]

        # Verify sorting: exact paths before parameterized, alphabetical within each group
        exact_paths = [p for p in route_paths if "{" not in p]
        param_paths = [p for p in route_paths if "{" in p]

        assert exact_paths == ["/health", "/status"]  # Sorted alphabetically
        assert param_paths == ["/items/{item_id}", "/users/{user_id}"]  # Sorted alphabetically

        # Verify exact paths come before parameterized paths
        health_index = route_paths.index("/health")
        status_index = route_paths.index("/status")
        items_index = route_paths.index("/items/{item_id}")
        users_index = route_paths.index("/users/{user_id}")

        assert health_index < items_index
        assert health_index < users_index
        assert status_index < items_index
        assert status_index < users_index

    def test_path_parameter_extraction(self):
        """Test path parameter extraction from route patterns."""
        router = Router()

        # Test various path patterns
        assert router.extract_path_params("/items") == []
        assert router.extract_path_params("/items/{item_id}") == ["item_id"]
        assert router.extract_path_params("/users/{user_id}/items/{item_id}") == ["user_id", "item_id"]
        assert router.extract_path_params("/complex/{a}/{b}/nested/{c}") == ["a", "b", "c"]

    def test_route_matching_directly(self):
        """Test route matching for both exact and parameterized paths."""
        router = Router()

        def dummy_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"test": "value"}

        # Add some test routes
        exact_route = RouteInfo(
            method=HTTPMethod.GET,
            endpoint=dummy_handler,
            signature=inspect.signature(dummy_handler),
            parameters={},
            type_hints={},
            path_params=[],
            description="Exact route",
        )

        param_route = RouteInfo(
            method=HTTPMethod.GET,
            endpoint=dummy_handler,
            signature=inspect.signature(dummy_handler),
            parameters={},
            type_hints={},
            path_params=["item_id"],
            description="Parameterized route",
        )

        router.register_route("/items/special", HTTPMethod.GET, exact_route)
        router.register_route("/items/{item_id}", HTTPMethod.GET, param_route)

        # Test exact match
        found_route, path_params = router.find_matching_route("/items/special", HTTPMethod.GET)
        assert found_route is not None
        assert found_route.description == "Exact route"
        assert path_params == {}

        # Test parameterized match
        found_route, path_params = router.find_matching_route("/items/123", HTTPMethod.GET)
        assert found_route is not None
        assert found_route.description == "Parameterized route"
        assert path_params == {"item_id": "123"}

        # Test no match
        found_route, path_params = router.find_matching_route("/nonexistent", HTTPMethod.GET)
        assert found_route is None
        assert path_params == {}

    def test_multiple_routers_independence(self):
        """Test that multiple routers work independently - demonstrates reusability!"""
        router1 = Router()
        router2 = Router()

        def handler1(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"router": "1"}

        def handler2(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"router": "2"}

        route_info1 = RouteInfo(
            method=HTTPMethod.GET,
            endpoint=handler1,
            signature=inspect.signature(handler1),
            parameters={},
            type_hints={},
            path_params=[],
            description="Router 1",
        )

        route_info2 = RouteInfo(
            method=HTTPMethod.GET,
            endpoint=handler2,
            signature=inspect.signature(handler2),
            parameters={},
            type_hints={},
            path_params=[],
            description="Router 2",
        )

        # Each router has different routes
        router1.register_route("/test", HTTPMethod.GET, route_info1)
        router2.register_route("/test", HTTPMethod.GET, route_info2)

        # They should be independent
        route1, _ = router1.find_matching_route("/test", HTTPMethod.GET)
        route2, _ = router2.find_matching_route("/test", HTTPMethod.GET)

        assert route1 is not None and route1.description == "Router 1"
        assert route2 is not None and route2.description == "Router 2"

        # One router's routes don't affect the other
        assert len(router1.routes) == 1
        assert len(router2.routes) == 1

    def test_sorted_routes_complex_ordering(self):
        """Test that sorted routes handles complex ordering scenarios correctly."""
        router = Router()

        def dummy_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"status": "ok"}

        def create_route_info(path_params: list[str]) -> RouteInfo:
            return RouteInfo(
                method=HTTPMethod.GET,
                endpoint=dummy_handler,
                signature=inspect.signature(dummy_handler),
                parameters={},
                type_hints={},
                path_params=path_params,
                description="Test route",
            )

        # Register routes to test sorting behavior
        router.register_route("/items/special", HTTPMethod.GET, create_route_info([]))  # exact
        router.register_route("/items/{item_id}", HTTPMethod.GET, create_route_info(["item_id"]))  # param
        router.register_route("/users", HTTPMethod.GET, create_route_info([]))  # exact

        sorted_routes = router.sorted_routes
        route_paths = [path for path, _ in sorted_routes]

        # Exact paths should come before parameterized paths
        # Within each category, they should be sorted alphabetically
        expected_paths = ["/items/special", "/users", "/items/{item_id}"]
        assert route_paths == expected_paths

    def test_mixed_order_route_registration_sorting(self):
        """Test that routes registered in mixed order are sorted correctly."""
        router = Router()

        def dummy_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"status": "ok"}

        def create_route_info(path_params: list[str]) -> RouteInfo:
            return RouteInfo(
                method=HTTPMethod.GET,
                endpoint=dummy_handler,
                signature=inspect.signature(dummy_handler),
                parameters={},
                type_hints={},
                path_params=path_params,
                description="Test route",
            )

        # Add routes in non-ideal order to verify sorting works
        router.register_route(
            "/items/{item_id}", HTTPMethod.GET, create_route_info(["item_id"])
        )  # param - should come later
        router.register_route("/items/special", HTTPMethod.GET, create_route_info([]))  # exact - should come first
        router.register_route(
            "/users/{user_id}", HTTPMethod.GET, create_route_info(["user_id"])
        )  # param - should come later
        router.register_route("/health", HTTPMethod.GET, create_route_info([]))  # exact - should come first

        # Get sorted routes and verify ordering
        sorted_routes = router.sorted_routes
        route_paths = [path for path, _ in sorted_routes]

        # All exact paths should come before all parameterized paths
        exact_paths = [p for p in route_paths if "{" not in p]
        param_paths = [p for p in route_paths if "{" in p]

        # Check that exact paths come first in the full list
        exact_indices = [route_paths.index(p) for p in exact_paths]
        param_indices = [route_paths.index(p) for p in param_paths]

        # All exact path indices should be less than all parameterized path indices
        assert all(e < p for e in exact_indices for p in param_indices), (
            f"Exact paths {exact_paths} should come before parameterized paths {param_paths} in {route_paths}"
        )

        # Within each category, paths should be sorted alphabetically
        assert exact_paths == sorted(exact_paths)
        assert param_paths == sorted(param_paths)

    def test_router_same_path_different_methods(self):
        """Test that Router can handle same path with different HTTP methods."""
        router = Router()

        def get_items_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"method": "GET", "action": "list_items"}

        def post_items_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"method": "POST", "action": "create_item"}

        # Create route info for both methods
        get_route_info = RouteInfo(
            method=HTTPMethod.GET,
            endpoint=get_items_handler,
            signature=inspect.signature(get_items_handler),
            parameters={},
            type_hints={},
            path_params=[],
            description="List all items",
        )

        post_route_info = RouteInfo(
            method=HTTPMethod.POST,
            endpoint=post_items_handler,
            signature=inspect.signature(post_items_handler),
            parameters={},
            type_hints={},
            path_params=[],
            description="Create new item",
        )

        # Register both methods for the same path
        router.register_route("/items", HTTPMethod.GET, get_route_info)
        router.register_route("/items", HTTPMethod.POST, post_route_info)

        # Verify both routes are stored
        assert "/items" in router.routes
        assert "GET" in router.routes["/items"]
        assert "POST" in router.routes["/items"]
        assert router.routes["/items"][HTTPMethod.GET] == get_route_info
        assert router.routes["/items"][HTTPMethod.POST] == post_route_info

        # Test finding GET route
        found_route, path_params = router.find_matching_route("/items", HTTPMethod.GET)
        assert found_route is not None
        assert found_route.description == "List all items"
        assert found_route.endpoint == get_items_handler
        assert path_params == {}

        # Test finding POST route
        found_route, path_params = router.find_matching_route("/items", HTTPMethod.POST)
        assert found_route is not None
        assert found_route.description == "Create new item"
        assert found_route.endpoint == post_items_handler
        assert path_params == {}

        # Test method not registered (PUT)
        found_route, path_params = router.find_matching_route("/items", HTTPMethod.PUT)
        assert found_route is None
        assert path_params == {}

    def test_router_parameterized_path_multiple_methods(self):
        """Test Router with parameterized paths and multiple HTTP methods."""
        router = Router()

        def get_item_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"method": "GET", "action": "get_item"}

        def put_item_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"method": "PUT", "action": "update_item"}

        # Create route info for both methods with path parameters
        get_route_info = RouteInfo(
            method=HTTPMethod.GET,
            endpoint=get_item_handler,
            signature=inspect.signature(get_item_handler),
            parameters={},
            type_hints={},
            path_params=["item_id"],
            description="Get item by ID",
        )

        put_route_info = RouteInfo(
            method=HTTPMethod.PUT,
            endpoint=put_item_handler,
            signature=inspect.signature(put_item_handler),
            parameters={},
            type_hints={},
            path_params=["item_id"],
            description="Update item",
        )

        # Register both methods for the same parameterized path
        router.register_route("/items/{item_id}", HTTPMethod.GET, get_route_info)
        router.register_route("/items/{item_id}", HTTPMethod.PUT, put_route_info)

        # Test GET with parameter extraction
        found_route, path_params = router.find_matching_route("/items/42", HTTPMethod.GET)
        assert found_route is not None
        assert found_route.description == "Get item by ID"
        assert found_route.endpoint == get_item_handler
        assert path_params == {"item_id": "42"}

        # Test PUT with parameter extraction
        found_route, path_params = router.find_matching_route("/items/99", HTTPMethod.PUT)
        assert found_route is not None
        assert found_route.description == "Update item"
        assert found_route.endpoint == put_item_handler
        assert path_params == {"item_id": "99"}

        # Test unsupported method (DELETE)
        found_route, path_params = router.find_matching_route("/items/42", HTTPMethod.DELETE)
        assert found_route is None
        assert path_params == {}


class TestStandaloneFindMatchingRoute:
    """Test the standalone find_matching_route function."""

    @staticmethod
    def create_sorted_routes(routes_data: list[tuple[str, dict[HTTPMethod, RouteInfo]]]) -> SortedRoutes:
        """Helper to create type-safe SortedRoutes for testing."""
        return SortedRoutes(routes_data)

    def test_exact_path_match(self):
        """Test exact path matching without parameters."""

        def dummy_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {}

        route_info = RouteInfo(
            method=HTTPMethod.GET,
            endpoint=dummy_handler,
            signature=inspect.signature(dummy_handler),
            parameters={},
            type_hints={},
            path_params=[],
            description="Test route",
        )

        sorted_routes = self.create_sorted_routes(
            [
                ("/items", {HTTPMethod.GET: route_info}),
                ("/users", {HTTPMethod.POST: route_info}),
            ]
        )

        # Test matching route
        found_route, path_params = find_matching_route(sorted_routes, "/items", HTTPMethod.GET)
        assert found_route is not None
        assert found_route.method == HTTPMethod.GET
        assert path_params == {}

        # Test non-matching path
        found_route, path_params = find_matching_route(sorted_routes, "/nonexistent", HTTPMethod.GET)
        assert found_route is None
        assert path_params == {}

        # Test non-matching method
        found_route, path_params = find_matching_route(sorted_routes, "/items", HTTPMethod.POST)
        assert found_route is None
        assert path_params == {}

    def test_path_parameter_matching(self):
        """Test path parameter extraction."""

        def dummy_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {}

        route_info = RouteInfo(
            method=HTTPMethod.GET,
            endpoint=dummy_handler,
            signature=inspect.signature(dummy_handler),
            parameters={},
            type_hints={},
            path_params=["item_id"],
            description="Test route",
        )

        sorted_routes = self.create_sorted_routes(
            [
                ("/items/{item_id}", {HTTPMethod.GET: route_info}),
            ]
        )

        # Test parameter extraction
        found_route, path_params = find_matching_route(sorted_routes, "/items/123", HTTPMethod.GET)
        assert found_route is not None
        assert path_params == {"item_id": "123"}

        # Test non-matching path
        found_route, path_params = find_matching_route(sorted_routes, "/items/123/extra", HTTPMethod.GET)
        assert found_route is None
        assert path_params == {}

    def test_type_safety_with_sorted_routes(self):
        """Test that SortedRoutes type provides proper type safety."""

        def dummy_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {}

        route_info = RouteInfo(
            method=HTTPMethod.GET,
            endpoint=dummy_handler,
            signature=inspect.signature(dummy_handler),
            parameters={},
            type_hints={},
            path_params=[],
            description="Type safety test",
        )

        # This is the correct way - using our helper
        proper_sorted_routes = self.create_sorted_routes(
            [
                ("/items", {HTTPMethod.GET: route_info}),
            ]
        )

        # This should work fine
        found_route, path_params = find_matching_route(proper_sorted_routes, "/items", HTTPMethod.GET)
        assert found_route is not None
        assert found_route.description == "Type safety test"
        assert path_params == {}

    def test_same_path_different_methods(self):
        """Test that the same path can have different handlers for different HTTP methods."""

        def get_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"method": "GET"}

        def post_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"method": "POST"}

        get_route_info = RouteInfo(
            method=HTTPMethod.GET,
            endpoint=get_handler,
            signature=inspect.signature(get_handler),
            parameters={},
            type_hints={},
            path_params=[],
            description="GET handler",
        )

        post_route_info = RouteInfo(
            method=HTTPMethod.POST,
            endpoint=post_handler,
            signature=inspect.signature(post_handler),
            parameters={},
            type_hints={},
            path_params=[],
            description="POST handler",
        )

        sorted_routes = self.create_sorted_routes(
            [
                ("/items", {HTTPMethod.GET: get_route_info, HTTPMethod.POST: post_route_info}),
            ]
        )

        # Test GET method
        found_route, path_params = find_matching_route(sorted_routes, "/items", HTTPMethod.GET)
        assert found_route is not None
        assert found_route.description == "GET handler"
        assert found_route.endpoint == get_handler
        assert path_params == {}

        # Test POST method
        found_route, path_params = find_matching_route(sorted_routes, "/items", HTTPMethod.POST)
        assert found_route is not None
        assert found_route.description == "POST handler"
        assert found_route.endpoint == post_handler
        assert path_params == {}

        # Test non-existent method (PUT)
        found_route, path_params = find_matching_route(sorted_routes, "/items", HTTPMethod.PUT)
        assert found_route is None
        assert path_params == {}

    def test_same_parameterized_path_different_methods(self):
        """Test that parameterized paths can have different handlers for different HTTP methods."""

        def get_item_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"method": "GET", "action": "retrieve"}

        def put_item_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"method": "PUT", "action": "update"}

        def delete_item_handler(
            *,
            client: CogniteClient,
            secrets: SecretsMapping | None = None,
            function_call_info: FunctionCallInfo | None = None,
            **params: object,
        ) -> dict[str, str]:
            return {"method": "DELETE", "action": "remove"}

        get_route_info = RouteInfo(
            method=HTTPMethod.GET,
            endpoint=get_item_handler,
            signature=inspect.signature(get_item_handler),
            parameters={},
            type_hints={},
            path_params=["item_id"],
            description="Get item by ID",
        )

        put_route_info = RouteInfo(
            method=HTTPMethod.PUT,
            endpoint=put_item_handler,
            signature=inspect.signature(put_item_handler),
            parameters={},
            type_hints={},
            path_params=["item_id"],
            description="Update item by ID",
        )

        delete_route_info = RouteInfo(
            method=HTTPMethod.DELETE,
            endpoint=delete_item_handler,
            signature=inspect.signature(delete_item_handler),
            parameters={},
            type_hints={},
            path_params=["item_id"],
            description="Delete item by ID",
        )

        sorted_routes = self.create_sorted_routes(
            [
                (
                    "/items/{item_id}",
                    {
                        HTTPMethod.GET: get_route_info,
                        HTTPMethod.PUT: put_route_info,
                        HTTPMethod.DELETE: delete_route_info,
                    },
                ),
            ]
        )

        # Test GET method with parameter extraction
        found_route, path_params = find_matching_route(sorted_routes, "/items/123", HTTPMethod.GET)
        assert found_route is not None
        assert found_route.description == "Get item by ID"
        assert found_route.endpoint == get_item_handler
        assert path_params == {"item_id": "123"}

        # Test PUT method with parameter extraction
        found_route, path_params = find_matching_route(sorted_routes, "/items/456", HTTPMethod.PUT)
        assert found_route is not None
        assert found_route.description == "Update item by ID"
        assert found_route.endpoint == put_item_handler
        assert path_params == {"item_id": "456"}

        # Test DELETE method with parameter extraction
        found_route, path_params = find_matching_route(sorted_routes, "/items/789", HTTPMethod.DELETE)
        assert found_route is not None
        assert found_route.description == "Delete item by ID"
        assert found_route.endpoint == delete_item_handler
        assert path_params == {"item_id": "789"}

        # Test non-existent method (POST)
        found_route, path_params = find_matching_route(sorted_routes, "/items/123", HTTPMethod.POST)
        assert found_route is None
        assert path_params == {}
