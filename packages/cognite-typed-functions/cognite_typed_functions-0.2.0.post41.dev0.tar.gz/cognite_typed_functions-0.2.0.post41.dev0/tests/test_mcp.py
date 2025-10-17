"""Tests for the new MCP composed apps architecture."""

from collections.abc import Mapping
from typing import Any, cast

from cognite.client import CogniteClient

from cognite_typed_functions import __version__
from cognite_typed_functions.app import FunctionApp, create_function_service
from cognite_typed_functions.mcp import MCPApp, MCPTool, create_mcp_app
from cognite_typed_functions.models import Json

from .conftest import TestItem as Item
from .conftest import TestItemResponse as ItemResponse


class TestMCPComposedArchitecture:
    """Test MCP functionality with the new composed apps approach."""

    def test_mcp_app_creation(self, mcp_app: FunctionApp) -> None:
        """Test MCP app is created correctly."""
        assert mcp_app.title == "MCP-test-server"
        assert mcp_app.version == __version__

        # Check tools storage exists - now it's a dict internally
        tools_dict: dict[str, MCPTool] = getattr(mcp_app, "_tools", {})
        assert isinstance(tools_dict, dict)
        assert len(tools_dict) == 0

    def test_tool_decorator_registration(self, mcp_app: MCPApp, test_app: FunctionApp) -> None:
        """Test that @mcp_app.tool() decorator registers functions correctly."""
        # Initially no tools
        tools = mcp_app.tools
        assert len(tools) == 0

        # Register a function as both route and MCP tool
        @test_app.get("/items/{item_id}")
        @mcp_app.tool(description="Get an item by ID")
        def get_item(client: CogniteClient, item_id: int) -> ItemResponse:
            """Get an item by its ID."""
            return ItemResponse(id=item_id, item=Item(name=f"Item {item_id}", price=100.0), total_price=100.0)

        # Check tool was registered
        tools = mcp_app.tools
        assert len(tools) == 1
        tool = tools[0]
        assert tool.name == "get_item"
        assert "Get an item by ID" in tool.description

    def test_mcp_endpoints_exist(self, mcp_app: FunctionApp) -> None:
        """Test that MCP app has the required endpoints."""
        # Check that MCP endpoints are registered
        routes = mcp_app.routes
        assert "/__mcp_tools__" in routes
        assert "/__mcp_call__/{tool_name}" in routes

    def test_composed_handler_integration(
        self, mock_client: CogniteClient, mcp_app: MCPApp, test_app: FunctionApp
    ) -> None:
        """Test that composed handler works with MCP and main apps."""

        # Register a test function
        @test_app.get("/test")
        @mcp_app.tool(description="Test function")
        def test_func(client: CogniteClient) -> dict[str, str]:
            return {"message": "test"}

        # Create composed handler
        handler = create_function_service(mcp_app, test_app)

        # Test MCP tools endpoint
        tools_response: Any = handler(client=mock_client, data={"path": "/__mcp_tools__", "method": "GET", "body": {}})

        assert tools_response["success"] is True
        data: Any = tools_response["data"]
        assert "tools" in data
        assert len(data["tools"]) == 1
        assert data["tools"][0]["name"] == "test_func"

        # Test regular route still works
        regular_response = handler(client=mock_client, data={"path": "/test", "method": "GET", "body": {}})
        assert isinstance(regular_response, dict)
        assert regular_response["success"] is True
        assert isinstance(regular_response["data"], dict)
        assert regular_response["data"]["message"] == "test"

    def test_mcp_tool_call_execution(self, mock_client: CogniteClient, mcp_app: MCPApp, test_app: FunctionApp) -> None:
        """Test that MCP tool calls work correctly."""

        # Register a function with parameters
        @test_app.post("/calculate")
        @mcp_app.tool(description="Calculate sum of two numbers")
        def calculate(client: CogniteClient, a: int, b: int) -> dict[str, int]:
            return {"result": a + b}

        # Create composed handler
        handler = create_function_service(mcp_app, test_app)

        # Test MCP tool call
        response: Any = handler(
            client=mock_client, data={"path": "/__mcp_call__/calculate", "method": "POST", "body": {"a": 5, "b": 3}}
        )

        # Check outer response wrapper
        assert response["success"] is True
        mcp_response = response["data"]
        assert isinstance(mcp_response, dict)
        assert isinstance(mcp_response["data"], dict)
        # Check inner MCP response
        assert mcp_response["success"] is True
        assert mcp_response["tool_name"] == "calculate"
        assert mcp_response["data"]["result"] == 8

    def test_tool_not_found_error(self, mock_client: CogniteClient, mcp_app: MCPApp, test_app: FunctionApp) -> None:
        """Test error handling when MCP tool is not found."""
        handler = create_function_service(mcp_app, test_app)

        # Test calling non-existent tool
        response: Any = handler(
            client=mock_client, data={"path": "/__mcp_call__/nonexistent", "method": "POST", "body": {}}
        )

        # Check outer response wrapper
        assert response["success"] is True
        error_response = response["data"]
        # Check inner MCP error response
        assert error_response["success"] is False
        assert error_response["error_type"] == "MCPToolNotFound"
        assert "nonexistent" in error_response["message"]

    def test_tool_decorator_with_docstring(self, mcp_app: MCPApp, test_app: FunctionApp) -> None:
        """Test that @mcp_app.tool() uses function docstring when no description provided."""

        @test_app.get("/items/{item_id}")
        @mcp_app.tool()  # No explicit description
        def get_item(client: CogniteClient, item_id: int) -> ItemResponse:
            """Get an item by its ID."""
            return ItemResponse(id=item_id, item=Item(name=f"Item {item_id}", price=100.0), total_price=100.0)

        tools = mcp_app.tools
        assert len(tools) == 1
        tool = tools[0]
        assert tool.name == "get_item"
        assert tool.description == "Get an item by its ID."

    def test_tool_decorator_with_no_docstring_or_description(self, mcp_app: MCPApp, test_app: FunctionApp) -> None:
        """Test that @mcp_app.tool() generates default description when no docstring available."""

        @test_app.post("/test")
        @mcp_app.tool()  # No explicit description, no docstring
        def no_docstring(client: CogniteClient, name: str) -> dict[str, str]:
            return {"name": name}

        tools = mcp_app.tools
        assert len(tools) == 1
        tool = tools[0]
        assert tool.name == "no_docstring"
        # Should generate a reasonable default description
        assert "no_docstring" in tool.description or "function" in tool.description.lower()

    def test_multiple_tools_registration(self, mcp_app: MCPApp, test_app: FunctionApp) -> None:
        """Test registering multiple tools on different routes."""

        @test_app.get("/users/{user_id}")
        @mcp_app.tool(description="Get user by ID")
        def get_user(client: CogniteClient, user_id: int) -> dict[str, Any]:
            return {"id": user_id, "name": f"User {user_id}"}

        @test_app.post("/users")
        @mcp_app.tool(description="Create new user")
        def create_user(client: CogniteClient, name: str, email: str) -> dict[str, Any]:
            return {"id": 123, "name": name, "email": email}

        @test_app.delete("/users/{user_id}")
        @mcp_app.tool(description="Delete user")
        def delete_user(client: CogniteClient, user_id: int) -> dict[str, str]:
            return {"status": "deleted"}

        # Check all tools registered
        tools = mcp_app.tools
        assert len(tools) == 3

        tool_names = {tool.name for tool in tools}
        assert "get_user" in tool_names
        assert "create_user" in tool_names
        assert "delete_user" in tool_names

    def test_mcp_tools_endpoint_with_multiple_tools(
        self, mock_client: CogniteClient, mcp_app: MCPApp, test_app: FunctionApp
    ) -> None:
        """Test /__mcp_tools__ endpoint lists all registered tools."""

        # Register multiple tools
        @test_app.get("/items/{item_id}")
        @mcp_app.tool(description="Get item details")
        def get_item(client: CogniteClient, item_id: int) -> ItemResponse:
            return ItemResponse(id=item_id, item=Item(name="Test", price=100.0), total_price=100.0)

        @test_app.post("/items")
        @mcp_app.tool(description="Create new item")
        def create_item(client: CogniteClient, item: Item) -> ItemResponse:
            return ItemResponse(id=456, item=item, total_price=item.price)

        handler = create_function_service(mcp_app, test_app)
        response: Any = handler(client=mock_client, data={"path": "/__mcp_tools__", "method": "GET", "body": {}})

        assert response["success"] is True
        data: Any = response["data"]
        assert "tools" in data
        assert len(data["tools"]) == 2

        tool_names = {tool["name"] for tool in data["tools"]}
        assert "get_item" in tool_names
        assert "create_item" in tool_names

    def test_mcp_tool_call_with_complex_parameters(
        self, mock_client: CogniteClient, mcp_app: MCPApp, test_app: FunctionApp
    ) -> None:
        """Test MCP tool call with complex parameter types including Pydantic models."""

        @test_app.post("/items")
        @mcp_app.tool(description="Create item with complex validation")
        def create_item_complex(
            client: CogniteClient, item: Item, quantity: int = 1, discount: float | None = None
        ) -> ItemResponse:
            total = item.price * quantity
            if discount:
                total = total * (1 - discount)
            return ItemResponse(id=789, item=item, total_price=total)

        handler = create_function_service(mcp_app, test_app)

        # Test with all parameters
        response: Any = handler(
            client=mock_client,
            data={
                "path": "/__mcp_call__/create_item_complex",
                "method": "POST",
                "body": {
                    "item": {"name": "Test Product", "price": 100.0},
                    "quantity": 2,
                    "discount": 0.1,  # 10% discount
                },
            },
        )

        assert response["success"] is True
        mcp_response = response["data"]
        assert isinstance(mcp_response, dict)
        assert isinstance(mcp_response["data"], dict)
        assert mcp_response["success"] is True
        assert mcp_response["data"]["total_price"] == 180.0  # (100 * 2) * 0.9

    def test_mcp_tool_call_with_optional_parameters(
        self, mock_client: CogniteClient, mcp_app: MCPApp, test_app: FunctionApp
    ) -> None:
        """Test MCP tool call with optional parameters not provided."""

        @test_app.get("/search")
        @mcp_app.tool(description="Search with optional filters")
        def search_items(
            client: CogniteClient, query: str, limit: int = 10, category: str | None = None
        ) -> dict[str, Any]:
            return {"query": query, "limit": limit, "category": category, "results": []}

        handler = create_function_service(mcp_app, test_app)

        # Test with only required parameter
        response: Any = handler(
            client=mock_client, data={"path": "/__mcp_call__/search_items", "method": "POST", "body": {"query": "test"}}
        )

        assert response["success"] is True
        mcp_response: Json = response["data"]
        assert isinstance(mcp_response, dict)
        assert isinstance(mcp_response["data"], dict)
        assert mcp_response["success"] is True
        assert isinstance(mcp_response["data"], Mapping)
        mcp_response["data"] = cast(Mapping[str, Any], mcp_response["data"])

        data = mcp_response["data"]
        assert data["query"] == "test"
        assert data["limit"] == 10  # Default value
        assert data["category"] is None  # Default None

    def test_mcp_tool_call_execution_error(
        self, mock_client: CogniteClient, mcp_app: MCPApp, test_app: FunctionApp
    ) -> None:
        """Test MCP tool call handles execution errors gracefully."""

        @test_app.post("/error")
        @mcp_app.tool(description="Function that raises error")
        def error_function(client: CogniteClient, should_fail: bool = True) -> dict[str, str]:
            if should_fail:
                raise ValueError("Intentional test error")
            return {"status": "ok"}

        handler = create_function_service(mcp_app, test_app)

        response: Any = handler(
            client=mock_client,
            data={"path": "/__mcp_call__/error_function", "method": "POST", "body": {"should_fail": True}},
        )

        assert response["success"] is True  # Handler doesn't fail
        error_response = response["data"]
        assert isinstance(error_response, dict)
        assert error_response["success"] is False  # But MCP response shows error
        assert error_response["error_type"] == "MCPExecutionError"
        assert isinstance(error_response["message"], str)
        assert "Intentional test error" in error_response["message"]

    def test_mcp_input_schema_generation(
        self, mock_client: CogniteClient, mcp_app: MCPApp, test_app: FunctionApp
    ) -> None:
        """Test that MCP tools include proper input schema for validation."""

        @test_app.post("/complex-function")
        @mcp_app.tool(description="Function with various parameter types")
        def complex_function(
            client: CogniteClient,
            name: str,
            age: int,
            height: float,
            is_active: bool = True,
            tags: list[str] | None = None,
            metadata: dict[str, Any] | None = None,
        ) -> dict[str, Any]:
            return {
                "name": name,
                "age": age,
                "height": height,
                "is_active": is_active,
                "tags": tags or [],
                "metadata": metadata or {},
            }

        handler = create_function_service(mcp_app, test_app)
        response: Any = handler(client=mock_client, data={"path": "/__mcp_tools__", "method": "GET", "body": {}})

        assert response["success"] is True
        assert isinstance(response["data"], dict)
        tools = response["data"]["tools"]
        assert len(tools) == 1

        tool = tools[0]
        schema = tool["inputSchema"]
        properties = schema["properties"]

        # Check that all parameters (except client) are in schema
        assert "name" in properties
        assert "age" in properties
        assert "height" in properties
        assert "is_active" in properties
        assert "tags" in properties
        assert "metadata" in properties
        assert "client" not in properties  # Should be excluded

        # Check required fields
        required = schema["required"]
        assert "name" in required
        assert "age" in required
        assert "height" in required
        assert "is_active" not in required  # Has default
        assert "tags" not in required  # Optional
        assert "metadata" not in required  # Optional

    def test_mcp_app_with_no_tools(self, mock_client: CogniteClient, mcp_app: MCPApp, test_app: FunctionApp) -> None:
        """Test MCP app behavior when no tools are registered."""
        handler = create_function_service(mcp_app, test_app)

        # Test tools endpoint with no tools
        response: Any = handler(client=mock_client, data={"path": "/__mcp_tools__", "method": "GET", "body": {}})

        assert response["success"] is True
        data: Any = response["data"]
        assert "tools" in data
        assert len(data["tools"]) == 0
        assert data["_meta"]["total_tools"] == 0

    def test_mcp_server_metadata(self, mock_client: CogniteClient, test_app: FunctionApp) -> None:
        """Test MCP server includes proper metadata in responses."""
        custom_mcp_app = create_mcp_app("custom-server")
        handler = create_function_service(custom_mcp_app, test_app)

        response: Any = handler(client=mock_client, data={"path": "/__mcp_tools__", "method": "GET", "body": {}})

        assert response["success"] is True
        data = response["data"]
        assert isinstance(data, dict)
        assert "_meta" in data
        meta = cast(Mapping[str, Any], data["_meta"])
        assert meta["server"] == "custom-server"
        assert "total_tools" in meta

    def test_composed_order_matters(self, mock_client: CogniteClient, test_app: FunctionApp) -> None:
        """Test that the order of apps in composition matters for route resolution."""
        # Create another app with conflicting route
        other_app = FunctionApp("Other App", "1.0.0")

        @test_app.get("/conflict")
        def main_conflict(client: CogniteClient) -> dict[str, str]:
            return {"source": "main"}

        @other_app.get("/conflict")
        def other_conflict(client: CogniteClient) -> dict[str, str]:
            return {"source": "other"}

        # Test different orders
        handler1 = create_function_service(test_app, other_app)  # main first
        handler2 = create_function_service(other_app, test_app)  # other first

        response1: Any = handler1(client=mock_client, data={"path": "/conflict", "method": "GET", "body": {}})
        response2: Any = handler2(client=mock_client, data={"path": "/conflict", "method": "GET", "body": {}})

        assert response1["success"] is True
        assert isinstance(response1["data"], dict)
        assert response1["data"]["source"] == "main"  # main_app was first

        assert response2["success"] is True
        assert isinstance(response2["data"], dict)
        assert response2["data"]["source"] == "other"  # other_app was first
