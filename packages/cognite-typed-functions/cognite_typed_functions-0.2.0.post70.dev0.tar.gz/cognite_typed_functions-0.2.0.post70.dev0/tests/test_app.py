"""Tests for FunctionApp class - the high-level decorator API and application functionality."""

from cognite.client import CogniteClient

from cognite_typed_functions.app import FunctionApp
from cognite_typed_functions.models import HTTPMethod

from .conftest import TestItem as Item
from .conftest import TestItemResponse as ItemResponse


class TestFunctionAppAPI:
    """Test FunctionApp's decorator API and high-level functionality."""

    def test_get_route_registration(self, test_app: FunctionApp, mock_client: CogniteClient):
        """Test that GET routes are properly registered."""

        @test_app.get("/items/{item_id}")
        def get_item(client: CogniteClient, item_id: int) -> ItemResponse:
            """Get an item by ID."""
            item = Item(name=f"Item {item_id}", price=100.0)
            return ItemResponse(id=item_id, item=item, total_price=100.0)

        # Check that route is registered
        assert "/items/{item_id}" in test_app.router.routes
        assert HTTPMethod.GET.value in test_app.router.routes["/items/{item_id}"]

        # Check route info
        route_info = test_app.router.routes["/items/{item_id}"][HTTPMethod.GET]
        assert route_info.method == HTTPMethod.GET
        assert route_info.endpoint == get_item
        assert route_info.description == "Get an item by ID."
        assert "item_id" in route_info.path_params

    def test_post_route_registration(self, test_app: FunctionApp):
        """Test that POST routes are properly registered."""

        @test_app.post("/items/")
        def create_item(client: CogniteClient, item: Item) -> ItemResponse:
            """Create a new item."""
            return ItemResponse(id=123, item=item, total_price=item.price)

        # Check that route is registered
        assert "/items/" in test_app.router.routes
        assert HTTPMethod.POST.value in test_app.router.routes["/items/"]

        # Check route info
        route_info = test_app.router.routes["/items/"][HTTPMethod.POST]
        assert route_info.method == HTTPMethod.POST.value
        assert route_info.endpoint == create_item
        assert route_info.description == "Create a new item."

    def test_multiple_methods_same_path(self, test_app: FunctionApp):
        """Test that multiple HTTP methods can be registered for the same path."""

        @test_app.get("/items/")
        def list_items(client: CogniteClient) -> list[ItemResponse]:
            """List all items."""
            return []

        @test_app.post("/items/")
        def create_item(client: CogniteClient, item: Item) -> ItemResponse:
            """Create a new item."""
            return ItemResponse(id=123, item=item, total_price=item.price)

        # Both methods should be registered for the same path
        assert "/items/" in test_app.router.routes
        assert HTTPMethod.GET.value in test_app.router.routes["/items/"]
        assert HTTPMethod.POST.value in test_app.router.routes["/items/"]

        # Each should have its own route info
        get_route = test_app.router.routes["/items/"][HTTPMethod.GET]
        post_route = test_app.router.routes["/items/"][HTTPMethod.POST]

        assert get_route.endpoint == list_items
        assert post_route.endpoint == create_item

    def test_path_parameter_extraction(self, test_app: FunctionApp):
        """Test extraction of path parameters from route patterns."""
        # Test single parameter
        single_params = test_app.extract_path_params("/items/{item_id}")
        assert single_params == ["item_id"]

        # Test multiple parameters
        multi_params = test_app.extract_path_params("/users/{user_id}/items/{item_id}")
        assert multi_params == ["user_id", "item_id"]

        # Test no parameters
        no_params = test_app.extract_path_params("/items/")
        assert no_params == []

    def test_post_method_registration_for_batch_operations(self, test_app: FunctionApp):
        """Test that POST method routes are properly registered for batch operations."""

        @test_app.post("/process/batch")
        def process_batch(client: CogniteClient, items: list[Item]) -> dict[str, int]:
            """Process items in batch."""
            return {"processed_count": len(items)}

        # Check that route is registered
        assert "/process/batch" in test_app.router.routes
        assert HTTPMethod.POST.value in test_app.router.routes["/process/batch"]

        # Check route info
        route_info = test_app.router.routes["/process/batch"][HTTPMethod.POST]
        assert route_info.method == HTTPMethod.POST.value
        assert route_info.endpoint == process_batch
        assert route_info.description == "Process items in batch."

    def test_function_signature_extraction(self, test_app: FunctionApp):
        """Test that function signatures are properly extracted.

        Note: All parameters (including dependencies) are stored in RouteInfo.
        Dependency filtering happens at execution time, not registration time.
        """

        @test_app.get("/items/{item_id}")
        def get_item(client: CogniteClient, item_id: int, include_tax: bool = False) -> ItemResponse:
            """Get an item by ID."""
            item = Item(name=f"Item {item_id}", price=100.0)
            return ItemResponse(id=item_id, item=item, total_price=100.0)

        route_info = test_app.router.routes["/items/{item_id}"][HTTPMethod.GET]

        # All parameters are stored in RouteInfo (filtering happens at execution time)
        assert "client" in route_info.parameters
        assert "item_id" in route_info.parameters
        assert "include_tax" in route_info.parameters

        # Check parameter details
        item_id_param = route_info.parameters["item_id"]
        assert item_id_param.annotation is int

        include_tax_param = route_info.parameters["include_tax"]
        assert include_tax_param.annotation is bool
        assert include_tax_param.default is False
