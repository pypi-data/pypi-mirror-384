"""Tests for dependency injection of client, secrets, and function_call_info.

These tests verify that the framework correctly implements dependency injection
for Cognite Function dependencies based on function signatures.
"""

import inspect
import logging
from collections.abc import Mapping
from typing import Any, cast
from unittest.mock import Mock

import pytest
from cognite.client import CogniteClient
from pydantic import BaseModel

from cognite_typed_functions.app import FunctionApp, create_function_service
from cognite_typed_functions.dependency_registry import DependencyRegistry
from cognite_typed_functions.models import ConfigurationError, FunctionCallInfo, SecretsMapping


class Item(BaseModel):
    """Test item model."""

    name: str
    price: float


class ItemResponse(BaseModel):
    """Test response model."""

    id: int
    name: str
    price: float
    has_secrets: bool
    has_call_info: bool


class TestDependencyInjection:
    """Test dependency injection for route handlers."""

    @pytest.fixture
    def mock_client(self) -> CogniteClient:
        """Mock CogniteClient for testing."""
        return Mock(spec=CogniteClient)

    @pytest.fixture
    def app(self) -> FunctionApp:
        """Create test app."""
        return FunctionApp(title="Test App", version="1.0.0")

    def test_handler_with_no_dependencies(self, app: FunctionApp, mock_client: CogniteClient):
        """Test handler that doesn't declare any dependency parameters."""

        @app.get("/items/{item_id}")
        def get_item(item_id: int) -> ItemResponse:
            """Handler with no dependencies."""
            return ItemResponse(
                id=item_id,
                name="Test Item",
                price=99.99,
                has_secrets=False,
                has_call_info=False,
            )

        handle = create_function_service(app)

        # Call the handler
        result = handle(
            client=mock_client,
            data={
                "path": "/items/123",
                "method": "GET",
            },
            secrets={"api_key": "secret123"},
            function_call_info={
                "function_id": "func123",
                "call_id": "call456",
                "schedule_id": None,
                "scheduled_time": None,
            },
        )
        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["data"] is not None
        assert isinstance(result["data"], dict)
        assert result["data"]["id"] == 123
        assert result["data"]["has_secrets"] is False
        assert result["data"]["has_call_info"] is False

    def test_handler_with_client_only(self, app: FunctionApp, mock_client: CogniteClient):
        """Test handler that only declares client parameter."""

        @app.get("/items/{item_id}")
        def get_item(client: CogniteClient, item_id: int) -> ItemResponse:
            """Handler with client only."""
            assert client is not None
            assert isinstance(client, Mock)
            return ItemResponse(
                id=item_id,
                name="Test Item",
                price=99.99,
                has_secrets=False,
                has_call_info=False,
            )

        handle = create_function_service(app)

        result = handle(
            client=mock_client,
            data={
                "path": "/items/456",
                "method": "GET",
            },
            secrets={"api_key": "secret123"},
            function_call_info={
                "function_id": "func123",
                "call_id": "call456",
                "schedule_id": None,
                "scheduled_time": None,
            },
        )

        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["data"] is not None
        assert isinstance(result["data"], dict)
        assert result["data"]["id"] == 456

    def test_handler_with_client_and_secrets(self, app: FunctionApp, mock_client: CogniteClient):
        """Test handler that declares client and secrets."""

        @app.get("/items/{item_id}")
        def get_item(
            client: CogniteClient,
            secrets: Mapping[str, str],
            item_id: int,
        ) -> ItemResponse:
            """Handler with client and secrets."""
            assert client is not None
            assert secrets is not None
            assert "api_key" in secrets
            assert secrets["api_key"] == "secret123"
            return ItemResponse(
                id=item_id,
                name="Test Item",
                price=99.99,
                has_secrets=True,
                has_call_info=False,
            )

        handle = create_function_service(app)

        result = handle(
            client=mock_client,
            data={
                "path": "/items/789",
                "method": "GET",
            },
            secrets={"api_key": "secret123"},
            function_call_info={
                "function_id": "func123",
                "call_id": "call456",
                "schedule_id": None,
                "scheduled_time": None,
            },
        )

        assert isinstance(result, dict)
        assert result["data"] is not None
        assert isinstance(result["data"], dict)
        assert result["success"] is True
        assert result["data"]["has_secrets"] is True

    def test_handler_with_all_dependencies(self, app: FunctionApp, mock_client: CogniteClient):
        """Test handler that declares all three dependency parameters."""

        @app.get("/items/{item_id}")
        def get_item(
            client: CogniteClient,
            secrets: Mapping[str, str],
            function_call_info: FunctionCallInfo,
            item_id: int,
        ) -> ItemResponse:
            """Handler with all dependencies."""
            assert client is not None
            assert secrets is not None
            assert function_call_info is not None
            assert function_call_info["function_id"] == "func123"
            assert function_call_info["call_id"] == "call456"
            return ItemResponse(
                id=item_id,
                name="Test Item",
                price=99.99,
                has_secrets=True,
                has_call_info=True,
            )

        handle = create_function_service(app)

        result = handle(
            client=mock_client,
            data={
                "path": "/items/999",
                "method": "GET",
            },
            secrets={"api_key": "secret123"},
            function_call_info={
                "function_id": "func123",
                "call_id": "call456",
                "schedule_id": None,
                "scheduled_time": None,
            },
        )

        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["data"] is not None
        assert isinstance(result["data"], dict)
        assert result["data"]["has_secrets"] is True
        assert result["data"]["has_call_info"] is True

    def test_handler_with_client_and_function_call_info(self, app: FunctionApp, mock_client: CogniteClient):
        """Test handler with client and function_call_info but no secrets."""

        @app.get("/items/{item_id}")
        def get_item(
            client: CogniteClient,
            function_call_info: FunctionCallInfo,
            item_id: int,
        ) -> ItemResponse:
            """Handler with client and function_call_info."""
            assert client is not None
            assert function_call_info is not None
            return ItemResponse(
                id=item_id,
                name="Test Item",
                price=99.99,
                has_secrets=False,
                has_call_info=True,
            )

        handle = create_function_service(app)

        result = handle(
            client=mock_client,
            data={
                "path": "/items/111",
                "method": "GET",
            },
            secrets={"api_key": "secret123"},
            function_call_info={
                "function_id": "func123",
                "call_id": "call456",
                "schedule_id": None,
                "scheduled_time": None,
            },
        )

        assert isinstance(result, dict)
        assert result["data"] is not None
        assert isinstance(result["data"], dict)
        assert result["success"] is True
        assert result["data"]["has_call_info"] is True

    def test_handler_parameter_order_flexibility(self, app: FunctionApp, mock_client: CogniteClient):
        """Test that dependency parameters can be declared in any order."""

        @app.post("/items")
        def create_item(
            item: Item,
            secrets: Mapping[str, str],
            client: CogniteClient,
        ) -> ItemResponse:
            """Handler with dependencies in non-standard order."""
            assert client is not None
            assert secrets is not None
            assert item.name == "Widget"
            return ItemResponse(
                id=1,
                name=item.name,
                price=item.price,
                has_secrets=True,
                has_call_info=False,
            )

        handle = create_function_service(app)

        result = handle(
            client=mock_client,
            data={
                "path": "/items",
                "method": "POST",
                "body": {"item": {"name": "Widget", "price": 29.99}},
            },
            secrets={"api_key": "secret123"},
        )

        assert isinstance(result, dict)
        assert result["data"] is not None
        assert isinstance(result["data"], dict)
        assert result["success"] is True
        assert result["data"]["name"] == "Widget"
        assert result["data"]["has_secrets"] is True

    def test_handler_without_client_when_none_provided(self, app: FunctionApp, mock_client: CogniteClient):
        """Test that handler without client parameter works even when client is provided."""

        @app.get("/ping")
        def ping() -> dict[str, str]:
            """Simple handler with no parameters at all."""
            return {"status": "pong"}

        handle = create_function_service(app)

        result = handle(
            client=mock_client,
            data={
                "path": "/ping",
                "method": "GET",
            },
        )

        assert isinstance(result, dict)
        assert result["data"] is not None
        assert isinstance(result["data"], dict)
        assert result["success"] is True
        assert result["data"]["status"] == "pong"

    def test_multiple_handlers_with_different_dependencies(self, app: FunctionApp, mock_client: CogniteClient):
        """Test that different handlers in the same app can have different dependencies."""

        @app.get("/public")
        def public_endpoint() -> dict[str, str]:
            """Public endpoint with no dependencies."""
            return {"type": "public"}

        @app.get("/authenticated")
        def authenticated_endpoint(client: CogniteClient) -> dict[str, str]:
            """Authenticated endpoint with client."""
            assert client is not None
            return {"type": "authenticated"}

        @app.get("/admin")
        def admin_endpoint(client: CogniteClient, secrets: Mapping[str, str]) -> dict[str, str]:
            """Admin endpoint with client and secrets."""
            assert client is not None
            assert secrets is not None
            return {"type": "admin"}

        handle = create_function_service(app)

        # Test public endpoint
        result1 = handle(client=mock_client, data={"path": "/public", "method": "GET"})
        assert isinstance(result1, dict)
        assert result1["data"] is not None
        assert isinstance(result1["data"], dict)
        assert result1["data"]["type"] == "public"

        # Test authenticated endpoint
        result2 = handle(client=mock_client, data={"path": "/authenticated", "method": "GET"})
        assert isinstance(result2, dict)
        assert result2["data"] is not None
        assert isinstance(result2["data"], dict)
        assert result2["data"]["type"] == "authenticated"

        # Test admin endpoint
        result3 = handle(
            client=mock_client,
            data={"path": "/admin", "method": "GET"},
            secrets={"admin_key": "secret"},
        )
        assert isinstance(result3, dict)
        assert result3["data"] is not None
        assert isinstance(result3["data"], dict)
        assert result3["data"]["type"] == "admin"

    def test_handler_with_optional_secrets_receives_empty_dict_when_none_provided(
        self, app: FunctionApp, mock_client: CogniteClient
    ):
        """Test that a handler declaring secrets receives an empty dict if secrets are None."""
        call_count = {"count": 0}

        @app.get("/items/{item_id}")
        def get_item(client: CogniteClient, secrets: Mapping[str, str], item_id: int) -> ItemResponse:
            """Handler that accepts secrets."""
            call_count["count"] += 1
            # Secrets should be an empty dict, not None
            assert secrets == {}
            return ItemResponse(
                id=item_id,
                name="Test",
                price=99.99,
                has_secrets=bool(secrets),  # bool({}) is False
                has_call_info=False,
            )

        handle = create_function_service(app)

        # Call with secrets=None
        result = handle(
            client=mock_client,
            data={"path": "/items/123", "method": "GET"},
            secrets=None,
        )
        assert isinstance(result, dict)
        assert result["data"] is not None
        assert isinstance(result["data"], dict)
        assert result["success"] is True
        assert call_count["count"] == 1
        assert result["data"]["has_secrets"] is False

    def test_custom_registry_merges_with_default_dependencies(self, mock_client: CogniteClient):
        """Test that custom dependencies work alongside default framework dependencies.

        With the new explicit registry approach, custom dependencies are added to
        the shared registry passed to create_function_service(), which automatically
        includes all default framework dependencies.
        """
        # Create a mock database service
        mock_database = Mock()
        mock_database.get_user.return_value = {"id": 1, "name": "Test User"}

        # Create app
        app = FunctionApp(
            title="Test App with Custom Registry",
            version="1.0.0",
        )

        # Register a handler that uses both built-in and custom dependencies
        @app.get("/user/{user_id}")
        def get_user(
            client: CogniteClient,
            secrets: Mapping[str, str],
            database: Mock,
            user_id: int,
        ) -> dict[str, object]:
            """Handler that uses both built-in and custom dependencies."""
            # Verify secrets is injected (client and database are guaranteed by types)
            assert secrets is not None

            # Use all dependencies
            user = database.get_user(user_id)

            return {
                "user_id": user_id,
                "user_name": user["name"],
                "has_client": True,
                "has_secrets": bool(secrets),
                "has_database": True,
            }

        # Create shared registry with both default and custom dependencies
        from cognite_typed_functions.dependency_registry import create_default_registry

        registry = create_default_registry()
        registry.register(
            lambda ctx: mock_database,
            target_type=Mock,
            param_name="database",
            description="Custom database service",
        )

        # Verify that all dependencies are available in the registry
        assert registry.is_dependency(
            "client", inspect.Parameter("client", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=CogniteClient)
        )
        assert registry.is_dependency(
            "secrets", inspect.Parameter("secrets", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=SecretsMapping)
        )
        assert registry.is_dependency(
            "function_call_info",
            inspect.Parameter(
                "function_call_info", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=FunctionCallInfo
            ),
        )
        assert registry.is_dependency(
            "logger", inspect.Parameter("logger", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=logging.Logger)
        )
        assert registry.is_dependency(
            "database", inspect.Parameter("database", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=Mock)
        )

        # Pass the registry to create_function_service (new explicit approach)
        handle = create_function_service(app, registry=registry)

        # Call the handler
        result = handle(
            client=mock_client,
            data={
                "path": "/user/1",
                "method": "GET",
            },
            secrets={"db_password": "secret"},
        )

        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["data"] is not None
        assert isinstance(result["data"], dict)
        assert result["data"]["user_id"] == 1
        assert result["data"]["user_name"] == "Test User"
        assert result["data"]["has_client"] is True
        assert result["data"]["has_secrets"] is True
        assert result["data"]["has_database"] is True

        # Verify database mock was called
        mock_database.get_user.assert_called_once_with(1)

    # NOTE: Override tests removed with new explicit registry approach
    # The new pattern doesn't support overriding default providers via duplicate registration.
    # If custom behavior is needed, build a custom registry from scratch instead of
    # using create_default_registry(), or use a different matching condition.


class TestDependencyMatchingStrategies:
    """Test type-based and name-based dependency matching strategies."""

    @pytest.fixture
    def mock_client(self) -> CogniteClient:
        """Mock CogniteClient for testing."""
        return Mock(spec=CogniteClient)

    def test_client_requires_both_name_and_type(self, mock_client: CogniteClient):
        """Test that CogniteClient injection requires BOTH name='client' AND type=CogniteClient (AND semantics).

        This test verifies that using a different parameter name like 'my_cdf_client'
        will NOT trigger dependency injection, even with the correct type annotation.
        """
        app = FunctionApp(title="Test App", version="1.0.0")

        @app.get("/items/{item_id}")
        def get_item(my_cdf_client: CogniteClient, item_id: int) -> dict[str, object]:
            """Handler with non-standard client parameter name - NOT a dependency."""
            # my_cdf_client is NOT injected, so this would fail if called
            # This parameter would need to come from request data
            return {"id": item_id, "client_param": str(type(my_cdf_client))}

        handle = create_function_service(app)

        # This will fail because my_cdf_client is not injected and not in request data
        result = handle(
            client=mock_client,
            data={
                "path": "/items/123",
                "method": "GET",
            },
        )

        data = cast(dict[str, Any], result)
        # Should fail with validation error about missing parameter
        assert data["success"] is False
        assert "my_cdf_client" in str(data)

    def test_secrets_requires_name_any_type(self, mock_client: CogniteClient):
        """Test that secrets injection requires name='secrets' but accepts any type annotation.

        This test verifies that using a different parameter name like 'api_keys'
        will NOT trigger dependency injection, even with a Mapping type annotation.
        """
        app = FunctionApp(title="Test App", version="1.0.0")

        @app.get("/items/{item_id}")
        def get_item(api_keys: Mapping[str, str], item_id: int) -> dict[str, object]:
            """Handler using Mapping type with custom parameter name - NOT a dependency."""
            # api_keys is NOT injected, would need to come from request data
            return {"id": item_id, "has_secrets": True}

        handle = create_function_service(app)

        # This will fail because api_keys is not injected and not in request data
        result = handle(
            client=mock_client,
            data={
                "path": "/items/456",
                "method": "GET",
            },
            secrets={"api_key": "secret123"},
        )

        data = cast(dict[str, Any], result)
        # Should fail with validation error about missing parameter
        assert data["success"] is False
        assert "api_keys" in str(data)

    def test_secrets_name_based_matching_with_mapping_type(self, mock_client: CogniteClient):
        """Test that secrets parameter name works with Mapping[str, str] type."""
        app = FunctionApp(title="Test App", version="1.0.0")

        @app.get("/items/{item_id}")
        def get_item(secrets: Mapping[str, str], item_id: int) -> dict[str, object]:
            """Handler using standard secrets parameter name."""
            assert secrets is not None
            assert secrets["api_key"] == "secret123"
            return {"id": item_id, "has_secrets": True}

        handle = create_function_service(app)

        result = handle(
            client=mock_client,
            data={
                "path": "/items/789",
                "method": "GET",
            },
            secrets={"api_key": "secret123"},
        )

        data = cast(dict[str, Any], result)
        assert data["success"] is True
        assert data["data"]["has_secrets"] is True

    def test_secrets_parameter_accepts_any_type_annotation(self, mock_client: CogniteClient):
        """Test that parameter named 'secrets' works with any type annotation.

        With AND semantics, 'secrets' is registered by name only, so it matches regardless
        of the type annotation used (dict, Mapping, dict[str, str], etc.). The value injected
        is always a plain dict from the context.
        """
        app = FunctionApp(title="Test App", version="1.0.0")

        @app.get("/items/{item_id}")
        def get_item(secrets: dict[str, str], item_id: int) -> dict[str, object]:
            """Handler using 'secrets' parameter name with dict[str, str] type annotation."""
            assert secrets is not None
            # With name-only matching, we get the plain dict from context
            assert isinstance(secrets, dict), f"Expected dict, got {type(secrets)}"
            assert secrets["api_key"] == "secret123"
            return {"id": item_id, "has_secrets": True, "type": type(secrets).__name__}

        handle = create_function_service(app)

        result = handle(
            client=mock_client,
            data={
                "path": "/items/999",
                "method": "GET",
            },
            secrets={"api_key": "secret123"},
        )

        data = cast(dict[str, Any], result)
        assert data["success"] is True
        assert data["data"]["has_secrets"] is True
        assert data["data"]["type"] == "dict"

    def test_logger_requires_both_name_and_type(self, mock_client: CogniteClient):
        """Test that logger injection requires BOTH name='logger' AND type=logging.Logger (AND semantics).

        This test verifies that using a different parameter name like 'log'
        will NOT trigger dependency injection, even with the correct type annotation.
        """
        app = FunctionApp(title="Test App", version="1.0.0")

        @app.get("/items/{item_id}")
        def get_item(log: logging.Logger, item_id: int) -> dict[str, object]:
            """Handler using 'log' instead of 'logger' - NOT a dependency."""
            # log is NOT injected, would need to come from request data
            return {"id": item_id, "has_logger": True}

        handle = create_function_service(app)

        # This will fail because log is not injected and not in request data
        result = handle(
            client=mock_client,
            data={
                "path": "/items/999",
                "method": "GET",
            },
        )

        data = cast(dict[str, Any], result)
        # Should fail with validation error about missing parameter
        assert data["success"] is False
        assert "log" in str(data)

    def test_custom_dependency_requires_consistent_naming(self, mock_client: CogniteClient):
        """Test that custom dependencies require consistent parameter naming across endpoints."""

        class DatabaseService:
            """Custom database service."""

            def get_data(self, id: int) -> str:
                return f"data_{id}"

        db_instance = DatabaseService()

        app = FunctionApp(title="Test App", version="1.0.0")

        @app.get("/items/{item_id}")
        def get_item(db: DatabaseService, item_id: int) -> dict[str, object]:
            """Handler using 'db' parameter name."""
            assert db is not None
            assert isinstance(db, DatabaseService)
            data = db.get_data(item_id)
            return {"id": item_id, "data": data}

        @app.get("/users/{user_id}")
        def get_user(db: DatabaseService, user_id: int) -> dict[str, object]:
            """Handler also using 'db' parameter name (consistent)."""
            assert db is not None
            assert isinstance(db, DatabaseService)
            data = db.get_data(user_id)
            return {"user_id": user_id, "data": data}

        # Create registry with custom dependency - now requires param_name
        from cognite_typed_functions.dependency_registry import create_default_registry

        registry = create_default_registry()
        registry.register(
            provider=lambda ctx: db_instance,
            target_type=DatabaseService,
            param_name="db",
            description="Database service (requires name='db' and type=DatabaseService)",
        )

        handle = create_function_service(app, registry=registry)

        # Test first endpoint
        result1 = handle(
            client=mock_client,
            data={
                "path": "/items/123",
                "method": "GET",
            },
        )

        data1 = cast(dict[str, Any], result1)
        assert data1["success"] is True
        assert data1["data"]["data"] == "data_123"

        # Test second endpoint with same parameter name
        result2 = handle(
            client=mock_client,
            data={
                "path": "/users/456",
                "method": "GET",
            },
        )

        data2 = cast(dict[str, Any], result2)
        assert data2["success"] is True
        assert data2["data"]["data"] == "data_456"

    def test_custom_dependency_name_based_matching(self, mock_client: CogniteClient):
        """Test custom dependency with name-based matching."""

        class ConfigService:
            """Custom config service."""

            def get_setting(self, key: str) -> str:
                return f"value_for_{key}"

        config_instance = ConfigService()

        app = FunctionApp(title="Test App", version="1.0.0")

        @app.get("/settings/{key}")
        def get_setting(config: ConfigService, key: str) -> dict[str, object]:
            """Handler that requires 'config' parameter name."""
            assert config is not None
            value = config.get_setting(key)
            return {"key": key, "value": value}

        # Create registry with custom dependency
        from cognite_typed_functions.dependency_registry import create_default_registry

        registry = create_default_registry()
        registry.register(
            provider=lambda ctx: config_instance,
            target_type=ConfigService,
            param_name="config",
            description="Configuration service (name-based)",
        )

        handle = create_function_service(app, registry=registry)

        result = handle(
            client=mock_client,
            data={
                "path": "/settings/timeout",
                "method": "GET",
            },
        )

        data = cast(dict[str, Any], result)
        assert data["success"] is True
        assert data["data"]["value"] == "value_for_timeout"

    def test_dependency_with_both_name_and_type_requires_both(self, mock_client: CogniteClient):
        """Test that dependency with both name and type specified requires BOTH to match (AND logic)."""

        class CacheService:
            """Custom cache service."""

            def __init__(self, name: str):
                self.name = name

        cache_instance = CacheService("main_cache")

        app = FunctionApp(title="Test App", version="1.0.0")

        # Should NOT match by name only (Item is the wrong type annotation)
        @app.get("/items/{item_id}")
        def get_item_by_name_only(cache: Item, item_id: int) -> dict[str, object]:
            """Handler with correct name but wrong type - NOT a dependency."""
            # cache is NOT injected, would need to come from request data
            return {"id": item_id, "has_cache": True}

        # Should NOT match by type only (wrong parameter name)
        @app.get("/users/{user_id}")
        def get_user_by_type_only(my_cache: CacheService, user_id: int) -> dict[str, object]:
            """Handler with correct type but wrong name - NOT a dependency."""
            # my_cache is NOT injected, would need to come from request data
            return {"user_id": user_id, "has_cache": True}

        # Should match with BOTH correct name AND type
        @app.get("/assets/{asset_id}")
        def get_asset_with_both(cache: CacheService, asset_id: int) -> dict[str, object]:
            """Handler with BOTH correct name and type - IS a dependency."""
            assert cache is not None
            assert isinstance(cache, CacheService)
            return {"asset_id": asset_id, "cache_name": cache.name, "matched": True}

        # Create registry with custom dependency
        from cognite_typed_functions.dependency_registry import create_default_registry

        registry = create_default_registry()
        registry.register(
            provider=lambda ctx: cache_instance,
            target_type=CacheService,
            param_name="cache",
            description="Cache service (requires BOTH param_name='cache' AND type=CacheService)",
        )

        handle = create_function_service(app, registry=registry)

        # Test name-only (should FAIL - needs both name and type)
        result1 = handle(
            client=mock_client,
            data={
                "path": "/items/123",
                "method": "GET",
            },
        )

        data1 = cast(dict[str, Any], result1)
        assert data1["success"] is False
        assert "cache" in str(data1)

        # Test type-only (should FAIL - needs both name and type)
        result2 = handle(
            client=mock_client,
            data={
                "path": "/users/456",
                "method": "GET",
            },
        )

        data2 = cast(dict[str, Any], result2)
        assert data2["success"] is False
        assert "my_cache" in str(data2)

        # Test both name AND type (should SUCCEED)
        result3 = handle(
            client=mock_client,
            data={
                "path": "/assets/789",
                "method": "GET",
            },
        )

        data3 = cast(dict[str, Any], result3)
        assert data3["success"] is True
        assert data3["data"]["matched"] is True
        assert data3["data"]["cache_name"] == "main_cache"

    def test_multiple_parameters_with_different_matching_strategies(self, mock_client: CogniteClient):
        """Test handler using multiple dependencies with AND semantics.

        Framework dependencies require strict name+type matching.
        Custom dependencies use type-only matching for flexible naming.
        """

        class MetricsService:
            """Custom metrics service."""

            def record(self, metric: str) -> None:
                pass

        metrics_instance = MetricsService()

        app = FunctionApp(title="Test App", version="1.0.0")

        @app.post("/items")
        def create_item(
            client: CogniteClient,  # Framework: requires name='client' AND type=CogniteClient
            secrets: Mapping[str, str],  # Framework: requires name='secrets', any type
            logger: logging.Logger,  # Framework: requires name='logger' AND type=logging.Logger
            metrics: MetricsService,  # Custom: type-based matching (any name works)
            item: Item,  # Regular parameter
        ) -> dict[str, object]:
            """Handler with multiple dependencies using correct framework names."""
            assert client is not None
            assert secrets is not None
            assert logger is not None
            assert metrics is not None
            assert item.name == "Widget"

            return {
                "name": item.name,
                "has_client": True,
                "has_secrets": bool(secrets),
                "has_logger": True,
                "has_metrics": True,
            }

        # Create registry with custom dependency
        from cognite_typed_functions.dependency_registry import create_default_registry

        registry = create_default_registry()
        registry.register(
            provider=lambda ctx: metrics_instance,
            target_type=MetricsService,
            param_name="metrics",
            description="Metrics service",
        )

        handle = create_function_service(app, registry=registry)

        result = handle(
            client=mock_client,
            data={
                "path": "/items",
                "method": "POST",
                "body": {"item": {"name": "Widget", "price": 29.99}},
            },
            secrets={"api_key": "secret"},
        )

        data = cast(dict[str, Any], result)
        assert data["success"] is True
        assert data["data"]["has_client"] is True
        assert data["data"]["has_secrets"] is True
        assert data["data"]["has_logger"] is True
        assert data["data"]["has_metrics"] is True


class TestDependencyRegistryValidation:
    """Test validation and error handling in dependency registry."""

    def test_register_requires_both_name_and_type(self):
        """Test that both param_name and target_type are required - this is a typed functions framework."""
        registry = DependencyRegistry()

        class MyService:
            pass

        # Both param_name and target_type are mandatory
        # This test verifies that valid registrations work with both specified
        registry.register(
            provider=lambda ctx: MyService(),
            target_type=MyService,
            param_name="service",
        )

        # Verify it's registered and matches with correct name and type
        param = inspect.Parameter("service", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=MyService)
        assert registry.is_dependency("service", param)

        # Should NOT match with wrong name
        param_wrong_name = inspect.Parameter(
            "other_service", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=MyService
        )
        assert not registry.is_dependency("other_service", param_wrong_name)

    def test_register_with_both_name_and_type_succeeds(self):
        """Test that registering with both name and type works with AND semantics."""

        class MyService:
            pass

        registry = DependencyRegistry()

        # Should not raise
        registry.register(
            provider=lambda ctx: MyService(),
            target_type=MyService,
            param_name="my_service",
        )

        # Check that it's registered with correct type and name
        dep_infos = registry.registered_dependencies
        assert any(d.param_name == "my_service" and d.target_type == MyService for d in dep_infos)

        # With AND semantics: name-only match should FAIL (needs both name AND type)
        param_by_name_only = inspect.Parameter("my_service", inspect.Parameter.POSITIONAL_OR_KEYWORD)
        assert not registry.is_dependency("my_service", param_by_name_only)

        # With AND semantics: type-only match should FAIL (needs both name AND type)
        param_by_type_only = inspect.Parameter(
            "other_name", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=MyService
        )
        assert not registry.is_dependency("other_name", param_by_type_only)

        # With AND semantics: BOTH name AND type must match
        param_with_both = inspect.Parameter("my_service", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=MyService)
        assert registry.is_dependency("my_service", param_with_both)

    def test_register_parameterized_list_with_param_name_succeeds(self):
        """Test that parameterized types work when combined with param_name."""
        registry = DependencyRegistry()

        # Should succeed - param_name makes it unambiguous
        registry.register(
            provider=lambda ctx: [1, 2, 3],
            target_type=list[int],
            param_name="default_ids",
        )

        # Verify it matches with BOTH param_name AND type
        param = inspect.Parameter("default_ids", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=list[int])
        assert registry.is_dependency("default_ids", param)

        # Should NOT match with wrong name
        param_wrong_name = inspect.Parameter("other_ids", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=list[int])
        assert not registry.is_dependency("other_ids", param_wrong_name)

    def test_register_custom_class_succeeds(self):
        """Test that registering custom classes requires param_name."""

        class CustomConfig:
            """Custom configuration class."""

            pass

        registry = DependencyRegistry()

        # Register custom class with param_name (now required)
        registry.register(
            provider=lambda ctx: CustomConfig(),
            target_type=CustomConfig,
            param_name="config",
        )

        # Verify it's registered with correct type and param_name
        dep_infos = registry.registered_dependencies
        assert any(d.target_type == CustomConfig and d.param_name == "config" for d in dep_infos)

        # Should match with correct name and type
        param = inspect.Parameter("config", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=CustomConfig)
        assert registry.is_dependency("config", param)

        # Should NOT match with wrong name
        param_wrong_name = inspect.Parameter(
            "other_config", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=CustomConfig
        )
        assert not registry.is_dependency("other_config", param_wrong_name)

    def test_register_param_name_with_generic_type_succeeds(self):
        """Test that param_name+type registration works with generic types like str."""
        registry = DependencyRegistry()

        # Should not raise - param_name+type registration is allowed even for generic types
        # The param_name makes it specific enough to avoid conflicts
        registry.register(
            provider=lambda ctx: "value",
            target_type=str,
            param_name="my_string_dep",
        )

        # Verify it's registered with correct type and name
        dep_infos = registry.registered_dependencies
        assert any(d.param_name == "my_string_dep" and d.target_type is str for d in dep_infos)

    def test_register_name_and_type_with_generic_types_succeeds(self):
        """Test that name+type registration works with generic types like int, str, dict."""
        registry = DependencyRegistry()

        # Should not raise - param_name+type registration is allowed even for generic types
        # The param_name makes it specific enough to avoid conflicts
        registry.register(
            provider=lambda ctx: 42,
            target_type=int,
            param_name="max_retries",
        )

        registry.register(
            provider=lambda ctx: "production",
            target_type=str,
            param_name="environment",
        )

        registry.register(
            provider=lambda ctx: {"key": "value"},
            target_type=dict,
            param_name="config",
        )

        # Verify they're registered with correct types and names
        dep_infos = registry.registered_dependencies
        assert any(d.param_name == "max_retries" and d.target_type is int for d in dep_infos)
        assert any(d.param_name == "environment" and d.target_type is str for d in dep_infos)
        assert any(d.param_name == "config" and d.target_type is dict for d in dep_infos)

        # Verify AND semantics: both name AND type must match
        param_max_retries = inspect.Parameter("max_retries", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=int)
        assert registry.is_dependency("max_retries", param_max_retries)

        # Wrong name -> not a dependency
        param_wrong_name = inspect.Parameter("retry_count", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=int)
        assert not registry.is_dependency("retry_count", param_wrong_name)

        # Wrong type -> not a dependency
        param_wrong_type = inspect.Parameter("max_retries", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=str)
        assert not registry.is_dependency("max_retries", param_wrong_type)

    def test_generic_abstract_type_with_name_succeeds(self):
        """Test that generic abstract types work when both name and type are specified."""
        registry = DependencyRegistry()

        # Should succeed - Mapping with param_name
        registry.register(
            provider=lambda ctx: {},
            target_type=dict,
            param_name="my_mapping",
            description="Test mapping",
        )

        # Verify it's registered
        dep_infos = registry.registered_dependencies
        assert any(d.param_name == "my_mapping" for d in dep_infos)

        # Test that it matches with both name AND Mapping-compatible type
        param_correct = inspect.Parameter(
            "my_mapping", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=dict[str, str]
        )
        assert registry.is_dependency("my_mapping", param_correct)

        # Should NOT match with wrong name (even if type is compatible)
        param_wrong_name = inspect.Parameter(
            "other_name", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=dict[str, str]
        )
        assert not registry.is_dependency("other_name", param_wrong_name)

        # Should NOT match with correct name but wrong type
        param_wrong_type = inspect.Parameter("my_mapping", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=str)
        assert not registry.is_dependency("my_mapping", param_wrong_type)

    def test_duplicate_registration_name_and_type_raises_error(self):
        """Test that registering duplicate name+type dependency raises ConfigurationError."""
        registry = DependencyRegistry()

        # First registration should succeed
        registry.register(
            provider=lambda ctx: 42,
            target_type=int,
            param_name="max_retries",
        )

        # Second registration with same name and type should fail
        with pytest.raises(ConfigurationError) as exc_info:
            registry.register(
                provider=lambda ctx: 100,
                target_type=int,
                param_name="max_retries",
            )

        error_message = str(exc_info.value)
        assert "already registered" in error_message
        assert "max_retries" in error_message
        assert "int" in error_message

    def test_different_names_same_type_succeeds(self):
        """Test that different param names with same type can be registered."""
        registry = DependencyRegistry()

        # Both should succeed - different param names
        registry.register(
            provider=lambda ctx: 42,
            target_type=int,
            param_name="max_retries",
        )

        registry.register(
            provider=lambda ctx: 100,
            target_type=int,
            param_name="timeout",
        )

        # Both should be registered with same type but different names
        dep_infos = registry.registered_dependencies
        assert any(d.param_name == "max_retries" and d.target_type is int for d in dep_infos)
        assert any(d.param_name == "timeout" and d.target_type is int for d in dep_infos)

    def test_same_name_different_types_succeeds(self):
        """Test that same param name with different types can be registered."""
        registry = DependencyRegistry()

        # Both should succeed - different types (even with same param_name is weird but allowed)
        registry.register(
            provider=lambda ctx: 42,
            target_type=int,
            param_name="config",
        )

        registry.register(
            provider=lambda ctx: "string",
            target_type=str,
            param_name="config",
        )

        # Both should be registered with same name but different types
        dep_infos = registry.registered_dependencies
        assert any(d.param_name == "config" and d.target_type is int for d in dep_infos)
        assert any(d.param_name == "config" and d.target_type is str for d in dep_infos)
