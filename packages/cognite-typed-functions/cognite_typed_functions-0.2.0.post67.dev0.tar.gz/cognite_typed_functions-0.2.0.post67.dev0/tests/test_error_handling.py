"""Tests for comprehensive error handling scenarios."""

import pytest
from cognite.client import CogniteClient

from cognite_typed_functions.app import FunctionApp, create_function_service
from cognite_typed_functions.models import CogniteTypedError, DataDict, Handle

from .conftest import TestItem as Item
from .conftest import TestItemResponse as ItemResponse


@pytest.fixture
def error_test_app() -> FunctionApp:
    """Create a test app with routes that can raise various errors."""
    app = FunctionApp(title="Error Test App", version="1.0.0")

    @app.get("/items/{item_id}")
    def get_item(client: CogniteClient, item_id: int) -> ItemResponse:
        """Get an item by ID - can raise various errors."""
        if item_id == 404:
            raise ValueError("Item not found")
        elif item_id == 500:
            raise RuntimeError("Internal server error")
        elif item_id == 999:
            # Return invalid data to test response validation
            item = Item(
                name="Invalid Item",
                price=-100,
            )  # This should fail validation
            return ItemResponse(id=item_id, item=item, total_price=-100)

        item = Item(name=f"Item {item_id}", price=100.0)
        return ItemResponse(id=item_id, item=item, total_price=100.0)

    @app.post("/items/")
    def create_item(client: CogniteClient, item: Item) -> ItemResponse:
        """Create an item - validates input."""
        total = item.price + (item.tax or 0)
        return ItemResponse(id=123, item=item, total_price=total)

    return app


@pytest.fixture
def error_test_handler(error_test_app: FunctionApp) -> Handle:
    """Create handler for error test app."""
    return create_function_service(error_test_app)


class TestErrorHandling:
    """Test comprehensive error handling scenarios."""

    def test_route_function_raises_value_error(self, error_test_handler: Handle, mock_client: CogniteClient):
        """Test handling when route function raises ValueError."""
        request_data: DataDict = {"path": "/items/404", "method": "GET", "body": {}}

        response = error_test_handler(client=mock_client, data=request_data)

        assert isinstance(response, dict)
        assert response["success"] is False
        assert response["error_type"] == "ExecutionError"
        assert isinstance(response["message"], str)
        assert "Item not found" in response["message"]

    def test_route_function_raises_runtime_error(self, error_test_handler: Handle, mock_client: CogniteClient):
        """Test handling when route function raises RuntimeError."""
        request_data: DataDict = {"path": "/items/500", "method": "GET", "body": {}}

        response = error_test_handler(client=mock_client, data=request_data)

        assert isinstance(response, dict)
        assert response["success"] is False
        assert response["error_type"] == "ExecutionError"
        assert isinstance(response["message"], str)
        assert "Internal server error" in response["message"]

    def test_pydantic_validation_error_on_input(self, error_test_handler: Handle, mock_client: CogniteClient):
        """Test Pydantic validation error on input data."""
        # Negative price should fail validation
        invalid_item_data: DataDict = {
            "name": "Invalid Item",
            "price": -50.0,  # Price must be > 0
        }

        request_data: DataDict = {
            "path": "/items/",
            "method": "POST",
            "body": {"item": invalid_item_data},
        }

        response = error_test_handler(client=mock_client, data=request_data)

        assert isinstance(response, dict)
        assert response["success"] is False
        assert response["error_type"] == "ValidationError"
        assert isinstance(response["message"], str)
        # Should contain validation error details
        assert "validation" in response["message"].lower() or "greater than" in response["message"].lower()

    def test_missing_required_field_validation(self, error_test_handler: Handle, mock_client: CogniteClient):
        """Test validation error for missing required fields."""
        # Missing required 'name' field
        invalid_item_data: DataDict = {
            "price": 100.0
            # Missing 'name' field
        }

        request_data: DataDict = {
            "path": "/items/",
            "method": "POST",
            "body": {"item": invalid_item_data},
        }

        response = error_test_handler(client=mock_client, data=request_data)

        assert isinstance(response, dict)
        assert response["success"] is False
        assert response["error_type"] == "ValidationError"

    def test_wrong_parameter_type_in_path(self, error_test_handler: Handle, mock_client: CogniteClient):
        """Test error when path parameter has wrong type."""
        request_data: DataDict = {
            "path": "/items/not-a-number",
            "method": "GET",
            "body": {},
        }

        response = error_test_handler(client=mock_client, data=request_data)

        assert isinstance(response, dict)
        assert response["success"] is False
        assert response["error_type"] == "ValidationError"

    def test_invalid_json_in_request_body(self, error_test_handler: Handle, mock_client: CogniteClient):
        """Test handling of completely invalid request structure."""
        # This should fail at the RequestData parsing level
        invalid_request: DataDict = {
            "path": 123,  # Should be string
            "method": "POST",
            "body": {},
        }

        response = error_test_handler(client=mock_client, data=invalid_request)
        assert isinstance(response, dict)

        assert response["success"] is False
        assert response["error_type"] == "ValidationError"

    def test_empty_path_handling(self, error_test_handler: Handle, mock_client: CogniteClient):
        """Test handling of empty or invalid paths."""
        request_data: DataDict = {"path": "", "method": "GET", "body": {}}

        response = error_test_handler(client=mock_client, data=request_data)

        assert isinstance(response, dict)
        # Should normalize to "/" and then return route not found
        assert response["success"] is False
        assert response["error_type"] == "RouteNotFound"

    def test_unsupported_http_method(self, error_test_handler: Handle, mock_client: CogniteClient):
        """Test handling of unsupported HTTP methods."""
        request_data: DataDict = {
            "path": "/items/123",
            "method": "PATCH",  # Not supported on this route
            "body": {},
        }

        response = error_test_handler(client=mock_client, data=request_data)

        assert isinstance(response, dict)
        assert response["success"] is False
        assert response["error_type"] == "ValidationError"

    def test_query_parameter_type_coercion(self, error_test_app: FunctionApp, mock_client: CogniteClient):
        """Test that query parameters are properly type-coerced."""

        # Add a route with query parameters
        @error_test_app.get("/items/search")
        def search_items(client: CogniteClient, limit: int = 10, active: bool = True) -> list[ItemResponse]:
            """Search items with query parameters."""
            return []

        # Recreate handler with new route
        handle = create_function_service(error_test_app)

        request_data: DataDict = {
            "path": "/items/search?limit=5&active=false",
            "method": "GET",
            "body": {},
        }

        response = handle(client=mock_client, data=request_data)
        assert isinstance(response, dict)
        # Should succeed with type coercion
        assert response["success"] is True
        assert response["data"] == []

    def test_missing_body_for_post_request(self, error_test_handler: Handle, mock_client: CogniteClient):
        """Test handling POST request with missing body."""
        request_data = {
            "path": "/items/",
            "method": "POST",
            # Missing 'body' key entirely
        }

        response = error_test_handler(client=mock_client, data=request_data)

        # Should handle gracefully with default empty body
        assert isinstance(response, dict)
        assert response["success"] is False
        assert response["error_type"] == "ExecutionError"

    def test_extra_fields_in_request_body(self, error_test_handler: Handle, mock_client: CogniteClient):
        """Test handling of extra fields in request body."""
        item_data = {
            "name": "Test Item",
            "price": 100.0,
            "extra_field": "should be ignored",  # Extra field
        }

        request_data: DataDict = {
            "path": "/items/",
            "method": "POST",
            "body": {"item": item_data},
        }

        response = error_test_handler(client=mock_client, data=request_data)

        # Should succeed, ignoring extra fields
        assert isinstance(response, dict)
        assert response["success"] is True
        assert isinstance(response["data"], dict)
        assert isinstance(response["data"]["item"], dict)
        assert response["data"]["item"]["name"] == "Test Item"
        # Extra field should not be in response
        assert "extra_field" not in response["data"]["item"]


class TestCogniteTypedErrorModel:
    """Test the CogniteTypedError model directly."""

    def test_error_model_creation_with_details(self):
        """Test creating error with details."""
        error = CogniteTypedError(
            error_type="CustomError",
            message="Something went wrong",
            details={"field": "price", "value": -100, "constraint": "must be positive"},
        )

        assert error.success is False
        assert error.error_type == "CustomError"
        assert error.message == "Something went wrong"
        assert error.details is not None
        assert error.details["field"] == "price"

    def test_error_model_without_details(self):
        """Test creating error without details."""
        error = CogniteTypedError(error_type="SimpleError", message="Simple error message")

        assert error.success is False
        assert error.error_type == "SimpleError"
        assert error.message == "Simple error message"
        assert error.details is None

    def test_error_model_serialization(self):
        """Test error model serialization."""
        error = CogniteTypedError(error_type="TestError", message="Test message", details={"key": "value"})

        serialized = error.model_dump()

        expected = {
            "success": False,
            "error_type": "TestError",
            "message": "Test message",
            "details": {"key": "value"},
        }

        assert serialized == expected
