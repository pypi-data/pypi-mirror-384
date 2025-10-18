"""Tests for the main handle function dispatcher."""

from typing import Any

from cognite.client import CogniteClient

from cognite_typed_functions.app import FunctionApp, create_function_service

from .conftest import TestItem as Item
from .conftest import TestItemResponse as ItemResponse


class TestHandleFunction:
    """Test the main handle function that dispatches requests."""

    def setup_method(self) -> None:
        """Set up test app with sample routes."""
        self.app = FunctionApp(title="Test App", version="1.0.0")

        # Add some test routes
        @self.app.get("/items/{item_id}")
        def get_item(client: CogniteClient, item_id: int, include_tax: bool = False) -> ItemResponse:
            """Get an item by ID."""
            tax = 10.0 if include_tax else None
            item = Item(name=f"Item {item_id}", price=100.0, tax=tax)
            total = item.price + (item.tax or 0)
            return ItemResponse(id=item_id, item=item, total_price=total)

        @self.app.post("/items/")
        def create_item(client: CogniteClient, item: Item) -> ItemResponse:
            """Create a new item."""
            total = item.price + (item.tax or 0)
            return ItemResponse(id=999, item=item, total_price=total)

        @self.app.post("/process/batch")
        def process_batch(client: CogniteClient, items: list[Item]) -> dict[str, int | float]:
            """Process multiple items in batch."""
            total_value = sum(item.price + (item.tax or 0) for item in items)
            return {"processed_count": len(items), "total_value": total_value}

        # Create the handler
        self.handle = create_function_service(self.app)

    def test_get_request_with_path_params(self, mock_client: CogniteClient) -> None:
        """Test GET request with path parameters."""
        request_data: dict[str, Any] = {
            "path": "/items/123?include_tax=true",
            "method": "GET",
            "body": {},
        }

        response = self.handle(client=mock_client, data=request_data)
        assert isinstance(response, dict)

        # Should return successful response
        assert response["success"] is True
        assert "data" in response

        # Check the returned data
        data = response["data"]
        assert isinstance(data, dict)
        assert data["id"] == 123
        assert isinstance(data["item"], dict)
        assert data["item"]["name"] == "Item 123"
        assert data["item"]["tax"] == 10.0  # include_tax=true
        assert data["total_price"] == 110.0

    def test_get_request_without_optional_params(self, mock_client: CogniteClient) -> None:
        """Test GET request without optional query parameters."""
        request_data: dict[str, Any] = {
            "path": "/items/456",
            "method": "GET",
            "body": {},
        }

        response = self.handle(client=mock_client, data=request_data)
        assert isinstance(response, dict)

        # Should return successful response
        assert response["success"] is True
        data = response["data"]
        assert isinstance(data, dict)
        assert data["id"] == 456
        assert isinstance(data["item"], dict)
        assert data["item"]["tax"] is None  # include_tax defaults to False
        assert data["total_price"] == 100.0

    def test_post_request_with_body(self, mock_client: CogniteClient) -> None:
        """Test POST request with request body."""
        item_data = {
            "name": "New Item",
            "description": "A new test item",
            "price": 50.0,
            "tax": 5.0,
        }

        request_data: dict[str, Any] = {
            "path": "/items/",
            "method": "POST",
            "body": {"item": item_data},
        }

        response = self.handle(client=mock_client, data=request_data)
        assert isinstance(response, dict)

        # Should return successful response
        assert response["success"] is True
        data = response["data"]
        assert isinstance(data, dict)
        assert isinstance(data["item"], dict)
        assert data["id"] == 999
        assert data["item"]["name"] == "New Item"
        assert data["item"]["price"] == 50.0
        assert data["total_price"] == 55.0

    def test_post_request_with_list_data(self, mock_client: CogniteClient) -> None:
        """Test POST request with list data for batch processing."""
        items_data = [
            {"name": "Item 1", "price": 100.0, "tax": 10.0},
            {"name": "Item 2", "price": 200.0, "tax": 20.0},
        ]

        request_data: dict[str, Any] = {
            "path": "/process/batch",
            "method": "POST",
            "body": {"items": items_data},
        }

        response = self.handle(client=mock_client, data=request_data)
        assert isinstance(response, dict)

        # Should return successful response
        assert response["success"] is True
        data = response["data"]
        assert isinstance(data, dict)
        assert data["processed_count"] == 2
        assert data["total_value"] == 330.0  # (100+10) + (200+20)

    def test_route_not_found_error(self, mock_client: CogniteClient) -> None:
        """Test error handling for non-existent routes."""
        request_data: dict[str, Any] = {
            "path": "/nonexistent/route",
            "method": "GET",
            "body": {},
        }

        response = self.handle(client=mock_client, data=request_data)
        assert isinstance(response, dict)

        # Should return error response
        assert response["success"] is False
        assert response["error_type"] == "RouteNotFound"
        assert isinstance(response["message"], str)
        assert "No route found" in response["message"]
        assert isinstance(response["details"], dict)
        assert "available_routes" in response["details"]

    def test_method_not_allowed_error(self, mock_client: CogniteClient) -> None:
        """Test error handling for unsupported methods on existing routes."""
        # Try DELETE on /items/123 (only GET is supported)
        request_data: dict[str, Any] = {
            "path": "/items/123",
            "method": "DELETE",
            "body": {},
        }

        response = self.handle(client=mock_client, data=request_data)

        # Should return error response
        assert isinstance(response, dict)
        assert response["success"] is False
        assert response["error_type"] == "RouteNotFound"

    def test_invalid_path_parameter_type(self, mock_client: CogniteClient) -> None:
        """Test error handling for invalid path parameter types."""
        # Try to pass string where int is expected
        request_data: dict[str, Any] = {
            "path": "/items/not-a-number",
            "method": "GET",
            "body": {},
        }

        response = self.handle(client=mock_client, data=request_data)

        # Should return error response
        assert isinstance(response, dict)
        assert response["success"] is False
        assert response["error_type"] == "ValidationError"

    def test_invalid_request_body(self, mock_client: CogniteClient) -> None:
        """Test error handling for invalid request body."""
        # Missing required field in item
        invalid_item_data: dict[str, Any] = {
            "name": "Item without price"
            # Missing required 'price' field
        }

        request_data: dict[str, Any] = {
            "path": "/items/",
            "method": "POST",
            "body": {"item": invalid_item_data},
        }

        response = self.handle(client=mock_client, data=request_data)

        # Should return error response
        assert isinstance(response, dict)
        assert response["success"] is False
        assert response["error_type"] == "ValidationError"

    def test_malformed_request_data(self, mock_client: CogniteClient) -> None:
        """Test error handling for malformed request data."""
        # Invalid request data structure
        invalid_request_data = {
            "path": "/items/123",
            "method": 123,  # Should be string
            "body": "not a dict",  # Should be dict
        }

        response: Any = self.handle(client=mock_client, data=invalid_request_data)

        # Should return error response
        assert response["success"] is False
        assert response["error_type"] == "ValidationError"

    def test_default_method_handling(self, mock_client: CogniteClient) -> None:
        """Test handling of default method (POST) when not specified."""
        request_data = {
            "path": "/process/batch",
            # No method specified, should default to POST
            "body": {"items": [{"name": "Item", "price": 100.0}]},
        }

        response = self.handle(client=mock_client, data=request_data)

        # Should work with default method
        assert isinstance(response, dict)
        assert response["success"] is True
        assert isinstance(response["data"], dict)
        assert response["data"]["processed_count"] == 1

    def test_client_parameter_injection(self, mock_client: CogniteClient) -> None:
        """Test that CogniteClient is properly injected into route functions."""

        # Add a route that uses the client
        @self.app.get("/client-test")
        def client_test(client: CogniteClient) -> dict[str, str]:
            """Test client injection."""
            return {"client_type": type(client).__name__}

        # Recreate handler with new route
        handle = create_function_service(self.app)

        request_data: dict[str, Any] = {
            "path": "/client-test",
            "method": "GET",
            "body": {},
        }

        response: Any = handle(client=mock_client, data=request_data)

        # Should work and show that client was injected
        assert response["success"] is True
        # The exact type might be Mock, but the important thing is it was passed
