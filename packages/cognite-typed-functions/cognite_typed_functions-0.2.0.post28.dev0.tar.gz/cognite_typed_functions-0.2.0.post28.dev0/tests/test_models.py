"""Tests for Pydantic model handling and validation."""

import pytest
from pydantic import ValidationError

from cognite_typed_functions.models import (
    CogniteTypedError,
    CogniteTypedResponse,
    HTTPMethod,
    RequestData,
)


class TestRequestDataParsing:
    """Test RequestData model parsing and validation."""

    def test_basic_path_parsing(self):
        """Test basic path parsing without query parameters."""
        request = RequestData(path="/items/123", method=HTTPMethod.GET)

        assert request.path == "/items/123"
        assert request.clean_path == "/items/123"
        assert request.method == "GET"
        assert request.query == {}
        assert request.body == {}

    def test_path_with_query_parameters(self):
        """Test parsing path with query parameters."""
        request = RequestData(path="/items/123?include_tax=true&limit=10", method=HTTPMethod.GET)

        assert request.path == "/items/123?include_tax=true&limit=10"
        assert request.clean_path == "/items/123"
        assert request.query == {"include_tax": "true", "limit": "10"}

    def test_query_parameters_with_multiple_values(self):
        """Test parsing query parameters with multiple values."""
        request = RequestData(path="/items?tags=electronics&tags=gadgets&category=tech", method=HTTPMethod.GET)

        assert request.clean_path == "/items"
        # Multiple values should be kept as lists
        assert request.query["tags"] == ["electronics", "gadgets"]
        assert request.query["category"] == "tech"

    def test_empty_query_parameters(self):
        """Test handling empty query parameters."""
        request = RequestData(path="/items?", method=HTTPMethod.GET)

        assert request.clean_path == "/items"
        assert request.query == {}

    def test_root_path_handling(self):
        """Test handling of root path."""
        request = RequestData(path="", method=HTTPMethod.GET)

        assert request.clean_path == "/"

    def test_default_values(self):
        """Test default values for RequestData."""
        request = RequestData()

        assert request.path == "/"
        assert request.clean_path == "/"
        assert request.method == HTTPMethod.POST
        assert request.body == {}
        assert request.query == {}

    def test_with_body_data(self):
        """Test RequestData with body data."""
        body_data = {"name": "Test Item", "price": 100.0}
        request = RequestData(path="/items/", method=HTTPMethod.POST, body=body_data)

        assert request.body == body_data
        assert request.clean_path == "/items/"


class TestHTTPMethod:
    """Test HTTPMethod enum."""

    def test_http_method_values(self):
        """Test HTTPMethod enum values."""
        assert HTTPMethod.GET.value == "GET"
        assert HTTPMethod.POST.value == "POST"
        assert HTTPMethod.PUT.value == "PUT"
        assert HTTPMethod.DELETE.value == "DELETE"

    def test_http_method_string_comparison(self):
        """Test HTTPMethod can be compared with strings."""
        assert HTTPMethod.GET == "GET"
        assert HTTPMethod.POST == "POST"


class TestErrorModels:
    """Test error response models."""

    def test_cognite_typed_error_creation(self):
        """Test creating CogniteTypedError."""
        error = CogniteTypedError(
            error_type="ValidationError",
            message="Invalid input data",
            details={"field": "price", "issue": "must be positive"},
        )

        assert error.success is False
        assert error.error_type == "ValidationError"
        assert error.message == "Invalid input data"
        assert error.details == {"field": "price", "issue": "must be positive"}

    def test_cognite_typed_error_serialization(self):
        """Test CogniteTypedError serialization to dict."""
        error = CogniteTypedError(error_type="NotFound", message="Item not found")

        error_dict = error.model_dump()
        expected = {
            "success": False,
            "error_type": "NotFound",
            "message": "Item not found",
            "details": None,
        }

        assert error_dict == expected

    def test_cognite_typed_response_creation(self):
        """Test creating CogniteTypedResponse."""
        data = {"id": 123, "name": "Test Item"}
        response = CogniteTypedResponse(data=data)

        assert response.success is True
        assert response.data == data

    def test_cognite_typed_response_serialization(self):
        """Test CogniteTypedResponse serialization to dict."""
        data = {"id": 123, "name": "Test Item"}
        response = CogniteTypedResponse(data=data)

        response_dict = response.model_dump()
        expected = {"success": True, "data": data}

        assert response_dict == expected


class TestModelValidation:
    """Test Pydantic model validation edge cases."""

    def test_request_data_validation_error(self):
        """Test RequestData validation with invalid data."""
        # Test with invalid method type
        with pytest.raises(ValidationError):
            RequestData(method=123)  # type: ignore Should be string

        # Test with invalid body type
        with pytest.raises(ValidationError):
            RequestData(body="not a dict")  # type: ignore Should be dict

    def test_empty_string_path_normalization(self):
        """Test that empty string paths are normalized to '/'."""
        request = RequestData(path="")
        assert request.clean_path == "/"

        request = RequestData(path="?query=value")
        assert request.clean_path == "/"
