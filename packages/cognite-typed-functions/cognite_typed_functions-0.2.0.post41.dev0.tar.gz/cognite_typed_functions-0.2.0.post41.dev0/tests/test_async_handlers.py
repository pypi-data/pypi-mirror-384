"""Tests for async route handlers."""

import asyncio
from typing import Any

from cognite.client import CogniteClient

from cognite_typed_functions.app import FunctionApp, create_function_service

from .conftest import TestItem as Item
from .conftest import TestItemResponse as ItemResponse


class TestAsyncHandlers:
    """Test async route handlers."""

    def setup_method(self) -> None:
        """Set up test app with both sync and async routes."""
        self.app = FunctionApp(title="Test Async App", version="1.0.0")

        # Sync route for comparison
        @self.app.get("/sync/items/{item_id}")
        def get_item_sync(client: CogniteClient, item_id: int) -> ItemResponse:
            """Get an item synchronously."""
            item = Item(name=f"Sync Item {item_id}", price=100.0)
            return ItemResponse(id=item_id, item=item, total_price=100.0)

        # Async route
        @self.app.get("/async/items/{item_id}")
        async def get_item_async(client: CogniteClient, item_id: int) -> ItemResponse:
            """Get an item asynchronously."""
            # Simulate async operation
            await asyncio.sleep(0.001)
            item = Item(name=f"Async Item {item_id}", price=200.0)
            return ItemResponse(id=item_id, item=item, total_price=200.0)

        # Async POST route
        @self.app.post("/async/items/")
        async def create_item_async(client: CogniteClient, item: Item) -> ItemResponse:
            """Create an item asynchronously."""
            await asyncio.sleep(0.001)
            total = item.price + (item.tax or 0)
            return ItemResponse(id=999, item=item, total_price=total)

        # Async route with multiple concurrent operations
        @self.app.get("/async/concurrent/{count}")
        async def concurrent_operations(client: CogniteClient, count: int) -> dict[str, Any]:
            """Perform concurrent async operations."""

            async def fetch_item(item_id: int) -> dict[str, Any]:
                await asyncio.sleep(0.001)
                return {"id": item_id, "name": f"Item {item_id}"}

            # Execute multiple operations concurrently
            items = await asyncio.gather(*[fetch_item(i) for i in range(count)])
            return {"items": items, "total": len(items)}

        # Create the handler
        self.handle = create_function_service(self.app)

    def test_async_get_request(self, mock_client: CogniteClient) -> None:
        """Test async GET request."""
        request_data: dict[str, Any] = {
            "path": "/async/items/123",
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
        assert data["item"]["name"] == "Async Item 123"
        assert data["item"]["price"] == 200.0
        assert data["total_price"] == 200.0

    def test_sync_get_request(self, mock_client: CogniteClient) -> None:
        """Test sync GET request still works."""
        request_data: dict[str, Any] = {
            "path": "/sync/items/456",
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
        assert data["item"]["name"] == "Sync Item 456"
        assert data["item"]["price"] == 100.0

    def test_async_post_request(self, mock_client: CogniteClient) -> None:
        """Test async POST request with body."""
        item_data = {
            "name": "Async Item",
            "description": "An async test item",
            "price": 75.0,
            "tax": 7.5,
        }

        request_data: dict[str, Any] = {
            "path": "/async/items/",
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
        assert data["item"]["name"] == "Async Item"
        assert data["total_price"] == 82.5

    def test_async_concurrent_operations(self, mock_client: CogniteClient) -> None:
        """Test async handler with concurrent operations."""
        request_data: dict[str, Any] = {
            "path": "/async/concurrent/5",
            "method": "GET",
            "body": {},
        }

        response = self.handle(client=mock_client, data=request_data)
        assert isinstance(response, dict)

        # Should return successful response
        assert response["success"] is True
        data = response["data"]
        assert isinstance(data, dict)
        assert isinstance(data["items"], list)
        assert data["total"] == 5
        assert len(data["items"]) == 5
        assert all(isinstance(item, dict) for item in data["items"])
        assert isinstance(data["items"][0], dict)
        assert data["items"][0]["id"] == 0
        assert isinstance(data["items"][4], dict)
        assert data["items"][4]["id"] == 4

    def test_async_error_handling(self, mock_client: CogniteClient) -> None:
        """Test error handling in async routes."""

        @self.app.get("/async/error")
        async def error_route(client: CogniteClient) -> dict[str, str]:
            """Route that raises an error."""
            await asyncio.sleep(0.001)
            raise ValueError("Async error test")

        # Recreate handler with new route
        handle = create_function_service(self.app)

        request_data: dict[str, Any] = {
            "path": "/async/error",
            "method": "GET",
            "body": {},
        }

        response = handle(client=mock_client, data=request_data)
        assert isinstance(response, dict)
        # Should return error response
        assert response["success"] is False
        assert response["error_type"] == "ExecutionError"
        assert isinstance(response["message"], str)
        assert "Async error test" in response["message"]


class TestAsyncComposition:
    """Test async handlers in composed apps."""

    def test_async_in_composed_apps(self, mock_client: CogniteClient) -> None:
        """Test that async handlers work across composed apps."""
        app1 = FunctionApp(title="App 1", version="1.0.0")
        app2 = FunctionApp(title="App 2", version="1.0.0")

        @app1.get("/app1/sync")
        def sync_route(client: CogniteClient) -> dict[str, str]:
            """Sync route in app1."""
            return {"app": "app1", "type": "sync"}

        @app2.get("/app2/async")
        async def async_route(client: CogniteClient) -> dict[str, str]:
            """Async route in app2."""
            await asyncio.sleep(0.001)
            return {"app": "app2", "type": "async"}

        # Compose apps
        handle = create_function_service(app1, app2)

        # Test sync route from app1
        response1 = handle(
            client=mock_client,
            data={"path": "/app1/sync", "method": "GET", "body": {}},
        )
        assert isinstance(response1, dict)
        assert response1["success"] is True
        assert isinstance(response1["data"], dict)
        assert response1["data"]["app"] == "app1"
        assert response1["data"]["type"] == "sync"

        # Test async route from app2
        response2 = handle(
            client=mock_client,
            data={"path": "/app2/async", "method": "GET", "body": {}},
        )
        assert isinstance(response2, dict)
        assert response2["success"] is True
        assert isinstance(response2["data"], dict)
        assert response2["success"] is True
        assert response2["data"]["app"] == "app2"
        assert response2["data"]["type"] == "async"

    def test_async_dispatch_between_apps(self, mock_client: CogniteClient) -> None:
        """Test that async dispatch works between composed apps."""
        app1 = FunctionApp(title="App 1", version="1.0.0")
        app2 = FunctionApp(title="App 2", version="1.0.0")

        @app1.get("/app1/data")
        async def get_data(client: CogniteClient) -> dict[str, int]:
            """Async route that returns data."""
            await asyncio.sleep(0.001)
            return {"value": 42}

        @app2.get("/app2/process")
        async def process_data(client: CogniteClient) -> dict[str, int]:
            """Async route that could dispatch to another app."""
            await asyncio.sleep(0.001)
            return {"result": 100}

        # Compose apps
        handle = create_function_service(app1, app2)

        # Both routes should work
        response1 = handle(
            client=mock_client,
            data={"path": "/app1/data", "method": "GET", "body": {}},
        )
        assert isinstance(response1, dict)
        assert isinstance(response1["data"], dict)
        assert response1["success"] is True
        assert response1["data"]["value"] == 42

        response2 = handle(
            client=mock_client,
            data={"path": "/app2/process", "method": "GET", "body": {}},
        )
        assert isinstance(response2, dict)
        assert isinstance(response2["data"], dict)
        assert response2["success"] is True
        assert response2["data"]["result"] == 100
