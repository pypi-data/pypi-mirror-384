"""Tests for the introspection composed apps architecture."""

from collections.abc import Mapping
from typing import Any, cast

from cognite.client import CogniteClient
from jsonschema_path.typing import Schema
from openapi_spec_validator import validate

from cognite_typed_functions import __version__
from cognite_typed_functions.app import FunctionApp, create_function_service
from cognite_typed_functions.mcp import create_mcp_app

from .conftest import TestItem as Item
from .conftest import TestItemResponse as ItemResponse


class TestIntrospectionComposedArchitecture:
    """Test introspection functionality with the new composed apps approach."""

    def test_introspection_app_creation(self, introspection_app: FunctionApp) -> None:
        """Test introspection app is created correctly."""
        assert introspection_app.title == "Introspection"
        assert introspection_app.version == __version__

    def test_introspection_endpoints_exist(self, introspection_app: FunctionApp) -> None:
        """Test that introspection app has the required endpoints."""
        routes = introspection_app.routes
        assert "/__schema__" in routes
        assert "/__routes__" in routes
        assert "/__health__" in routes
        assert "/__ping__" in routes

    def test_ping_endpoint(self, mock_client: CogniteClient, introspection_app: FunctionApp) -> None:
        """Test /__ping__ endpoint returns empty response."""
        handler = create_function_service(introspection_app)

        response = handler(client=mock_client, data={"path": "/__ping__", "method": "GET", "body": {}})
        assert isinstance(response, dict)
        assert response["success"] is True
        assert response["data"] == {}

    def test_health_endpoint_standalone(self, mock_client: CogniteClient, introspection_app: FunctionApp) -> None:
        """Test /__health__ endpoint with standalone introspection app."""
        handler = create_function_service(introspection_app)

        response = handler(client=mock_client, data={"path": "/__health__", "method": "GET", "body": {}})
        assert isinstance(response, dict)
        assert response["success"] is True
        health_data = response["data"]
        assert isinstance(health_data, dict)
        assert health_data["status"] == "healthy"
        # When introspection is standalone, it shows generic name since it's designed to show main app info
        assert health_data["app"] == "Introspection"
        assert health_data["version"] == __version__
        assert "composed_apps" in health_data
        assert "statistics" in health_data

    def test_health_endpoint_with_composed_apps(
        self, mock_client: CogniteClient, introspection_app: FunctionApp, test_app: FunctionApp
    ) -> None:
        """Test /__health__ endpoint shows information from all composed apps."""

        # Add a route to main app
        @test_app.get("/test")
        def test_route(client: CogniteClient) -> dict[str, str]:
            return {"message": "test"}

        handler = create_function_service(introspection_app, test_app)

        response = handler(client=mock_client, data={"path": "/__health__", "method": "GET", "body": {}})
        assert isinstance(response, dict)
        assert response["success"] is True
        health_data: Any = response["data"]
        assert isinstance(health_data, dict)
        assert health_data["status"] == "healthy"
        # Should show main app as primary
        assert health_data["app"] == "Test App"
        assert health_data["version"] == "1.0.0"
        health_data["composed_apps"] = cast(list[dict[str, Any]], health_data["composed_apps"])
        assert len(health_data["composed_apps"]) == 2  # Introspection + Test App
        assert health_data["statistics"]["total_routes"] >= 5  # 4 introspection routes + 1 test route

    def test_routes_endpoint_standalone(self, mock_client: CogniteClient, introspection_app: FunctionApp) -> None:
        """Test /__routes__ endpoint with standalone introspection app."""
        handler = create_function_service(introspection_app)

        response = handler(client=mock_client, data={"path": "/__routes__", "method": "GET", "body": {}})
        assert isinstance(response, dict)
        assert response["success"] is True
        response = cast(dict[str, dict[str, Any]], response)
        routes_data = response["data"]
        assert isinstance(routes_data, dict)
        assert "app_info" in routes_data
        assert "routes" in routes_data
        # Should include the introspection routes themselves
        routes = cast(dict[str, Any], routes_data["routes"])
        assert isinstance(routes, dict)
        assert "/__schema__" in routes
        assert "/__routes__" in routes
        assert "/__health__" in routes
        assert "/__ping__" in routes

    def test_routes_endpoint_with_composed_apps(
        self, mock_client: CogniteClient, introspection_app: FunctionApp, test_app: FunctionApp
    ) -> None:
        """Test /__routes__ endpoint shows routes from all composed apps."""

        # Add routes to main app
        @test_app.get("/users/{user_id}")
        def get_user(client: CogniteClient, user_id: int) -> dict[str, Any]:
            return {"id": user_id, "name": "User"}

        @test_app.post("/users")
        def create_user(client: CogniteClient, name: str) -> dict[str, Any]:
            return {"id": 123, "name": name}

        handler = create_function_service(introspection_app, test_app)

        response = handler(client=mock_client, data={"path": "/__routes__", "method": "GET", "body": {}})
        assert isinstance(response, dict)
        assert response["success"] is True
        routes_data = response["data"]
        assert isinstance(routes_data, dict)
        routes: Any = routes_data["routes"]
        assert isinstance(routes, dict)
        # Should include both introspection and main app routes
        assert "/__schema__" in routes
        assert "/users/{user_id}" in routes
        assert "/users" in routes

        # Check route methods
        assert "GET" in routes["/users/{user_id}"]["methods"]
        assert "POST" in routes["/users"]["methods"]

    def test_schema_endpoint_standalone(self, mock_client: CogniteClient, introspection_app: FunctionApp) -> None:
        """Test /__schema__ endpoint with standalone introspection app."""
        handler = create_function_service(introspection_app)

        response = handler(client=mock_client, data={"path": "/__schema__", "method": "GET", "body": {}})
        assert isinstance(response, dict)
        assert response["success"] is True
        schema_data: Any = response["data"]

        # Basic OpenAPI schema structure
        assert "openapi" in schema_data
        assert "info" in schema_data
        assert "paths" in schema_data

        # Should include introspection endpoints
        paths: Any = schema_data["paths"]
        assert "/__schema__" in paths
        assert "/__health__" in paths

        # Validate that the schema is valid OpenAPI 3.1 spec
        validate(cast(Schema, schema_data))
        assert schema_data["openapi"].startswith("3.1")
        assert "info" in schema_data
        assert "paths" in schema_data

    def test_schema_endpoint_with_composed_apps(
        self, mock_client: CogniteClient, introspection_app: FunctionApp, test_app: FunctionApp
    ) -> None:
        """Test /__schema__ endpoint generates schema for all composed apps."""

        # Add a route with Pydantic models
        @test_app.get("/items/{item_id}")
        def get_item(client: CogniteClient, item_id: int) -> ItemResponse:
            return ItemResponse(id=item_id, item=Item(name="Test Item", price=100.0), total_price=100.0)

        handler = create_function_service(introspection_app, test_app)

        response = handler(client=mock_client, data={"path": "/__schema__", "method": "GET", "body": {}})
        assert isinstance(response, dict)
        assert response["success"] is True
        schema_data: Any = response["data"]

        # Should use main app info
        assert schema_data["info"]["title"] == "Test App"
        assert schema_data["info"]["version"] == "1.0.0"

        # Should include all routes
        paths = schema_data["paths"]
        assert "/__schema__" in paths
        assert "/items/{item_id}" in paths

        # Should include Pydantic model components
        if "components" in schema_data:
            assert "schemas" in schema_data["components"]

        # Validate that the schema is valid OpenAPI 3.1 spec
        validate(cast(Schema, schema_data))
        assert schema_data["openapi"].startswith("3.1")
        assert "info" in schema_data
        assert "paths" in schema_data

    def test_openapi_schema_validation_comprehensive(
        self, mock_client: CogniteClient, introspection_app: FunctionApp, test_app: FunctionApp
    ) -> None:
        """Test comprehensive OpenAPI schema validation with complex routes and models."""

        # Add routes with various parameter types and Pydantic models
        @test_app.get("/items/{item_id}")
        def get_item(client: CogniteClient, item_id: int, include_tax: bool = False) -> ItemResponse:
            """Get an item by ID with optional tax calculation."""
            return ItemResponse(id=item_id, item=Item(name="Test Item", price=100.0), total_price=100.0)

        @test_app.post("/items")
        def create_item(
            client: CogniteClient,
            item: Item,
            quantity: int = 1,
            tags: list[str] | None = None,
            metadata: dict[str, Any] | None = None,
        ) -> ItemResponse:
            """Create a new item with optional quantity and metadata."""
            return ItemResponse(id=123, item=item, total_price=item.price * quantity)

        @test_app.put("/items/{item_id}")
        def update_item(client: CogniteClient, item_id: int, item: Item) -> ItemResponse:
            """Update an existing item."""
            return ItemResponse(id=item_id, item=item, total_price=item.price)

        @test_app.delete("/items/{item_id}")
        def delete_item(client: CogniteClient, item_id: int) -> dict[str, str]:
            """Delete an item by ID."""
            return {"status": "deleted", "id": str(item_id)}

        # Create handler with multiple apps for full composition testing
        handler = create_function_service(introspection_app, test_app)

        # Get the generated schema
        response = handler(client=mock_client, data={"path": "/__schema__", "method": "GET", "body": {}})
        assert isinstance(response, dict)
        assert response["success"] is True
        schema_data: Any = response["data"]

        # Comprehensive OpenAPI spec validation
        validate(cast(Schema, schema_data))
        assert schema_data["openapi"].startswith("3.1")
        assert "info" in schema_data
        assert "paths" in schema_data

        # Verify all our routes are present
        paths = schema_data["paths"]
        assert "/items/{item_id}" in paths
        assert "/items" in paths

        # Verify HTTP methods are correctly documented
        assert "get" in paths["/items/{item_id}"]
        assert "put" in paths["/items/{item_id}"]
        assert "delete" in paths["/items/{item_id}"]
        assert "post" in paths["/items"]

        # Verify that schema components exist and basic validation works
        if "components" in schema_data and "schemas" in schema_data["components"]:
            schemas = schema_data["components"]["schemas"]
            # Check that we have some schema components (at minimum our framework models)
            assert len(schemas) > 0, "No schema components found"
            # Verify common framework schemas are present
            assert "CogniteTypedResponse" in schemas or "CogniteTypedError" in schemas, (
                f"Framework models missing from {list(schemas.keys())}"
            )

    # Enable when MCP is implemented
    def test_full_composed_integration(
        self, mock_client: CogniteClient, introspection_app: FunctionApp, test_app: FunctionApp
    ) -> None:
        """Test introspection works with full composed architecture (MCP + Introspection + Main)."""
        # Create all three app types
        mcp_app = create_mcp_app("test-server")

        # Add a route that's both regular and MCP tool
        @test_app.get("/calculate/{a}/{b}")
        @mcp_app.tool(description="Add two numbers")
        def add_numbers(client: CogniteClient, a: int, b: int) -> dict[str, int]:
            return {"result": a + b}

        handler = create_function_service(introspection_app, mcp_app, test_app)

        # Test health endpoint sees all apps when introspection is first
        health_response = handler(client=mock_client, data={"path": "/__health__", "method": "GET", "body": {}})
        assert isinstance(health_response, dict)
        assert health_response["success"] is True
        health_data = health_response["data"]
        assert isinstance(health_data, dict)
        health_data["composed_apps"] = cast(list[dict[str, Any]], health_data["composed_apps"])
        assert len(health_data["composed_apps"]) == 3  # Introspection + MCP + Test App
        app_names = [app["name"] for app in health_data["composed_apps"]]
        assert "Introspection" in app_names
        assert "MCP-test-server" in app_names
        assert "Test App" in app_names

        # Test routes endpoint sees routes from all apps
        routes_response = handler(client=mock_client, data={"path": "/__routes__", "method": "GET", "body": {}})
        assert isinstance(routes_response, dict)
        assert routes_response["success"] is True
        routes_data = routes_response["data"]
        assert isinstance(routes_data, dict)
        assert isinstance(routes_data["routes"], Mapping)
        assert isinstance(routes_response["data"], dict)
        routes = routes_response["data"]["routes"]

        # Should see MCP routes
        assert isinstance(routes, dict)
        assert "/__mcp_tools__" in routes
        assert "/__mcp_call__/{tool_name}" in routes

        # Should see introspection routes
        assert "/__health__" in routes

        # Should see main app routes
        assert "/calculate/{a}/{b}" in routes

        # Test schema includes everything and is valid
        schema_response = handler(client=mock_client, data={"path": "/__schema__", "method": "GET", "body": {}})
        assert isinstance(schema_response, dict)
        assert schema_response["success"] is True
        schema_data = schema_response["data"]
        assert isinstance(schema_data, Mapping)
        schema_paths = schema_data["paths"]
        assert isinstance(schema_paths, dict)
        assert len(schema_paths) >= 5  # MCP + introspection + main app routes

        # Validate that the composed schema is valid OpenAPI spec
        validate(cast(Schema, schema_data))
        assert isinstance(schema_data["openapi"], str)
        assert schema_data["openapi"].startswith("3.1")
        assert "info" in schema_data
        assert "paths" in schema_data

    def test_introspection_error_handling(self, mock_client: CogniteClient, introspection_app: FunctionApp) -> None:
        """Test introspection endpoints handle errors gracefully."""
        # This tests that introspection works even when there are issues with route access
        handler = create_function_service(introspection_app)

        # All endpoints should work even with minimal setup
        for endpoint in ["/__ping__", "/__health__", "/__routes__", "/__schema__"]:
            response = handler(client=mock_client, data={"path": endpoint, "method": "GET", "body": {}})
            assert isinstance(response, dict)
            assert response["success"] is True, f"Endpoint {endpoint} failed"

            # Additional validation for schema endpoint
            if endpoint == "/__schema__":
                schema_data: Any = response["data"]
                # Even with minimal setup, schema should be valid OpenAPI spec
                validate(cast(Schema, schema_data))
                assert schema_data["openapi"].startswith("3.1")
                assert "info" in schema_data
                assert "paths" in schema_data

    def test_introspection_with_no_main_app_routes(
        self, mock_client: CogniteClient, introspection_app: FunctionApp
    ) -> None:
        """Test introspection when main app has no routes."""
        empty_app = FunctionApp("Empty App", "1.0.0")
        handler = create_function_service(introspection_app, empty_app)

        # Health should still work
        health_response = handler(client=mock_client, data={"path": "/__health__", "method": "GET", "body": {}})
        assert isinstance(health_response, dict)
        assert health_response["success"] is True
        health_data: Any = health_response["data"]
        assert isinstance(health_data, dict)
        assert health_data["app"] == "Empty App"  # Should identify empty app as main
        assert health_data["statistics"]["total_routes"] >= 4  # At least introspection routes
