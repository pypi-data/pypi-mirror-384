"""Tests for dependency injection of client, secrets, and function_call_info.

These tests verify that the framework correctly implements dependency injection
for Cognite Function dependencies based on function signatures.
"""

import inspect
import logging
from collections.abc import Mapping
from typing import Any, Dict, List, cast  # noqa: UP035 - Testing deprecated types intentionally
from unittest.mock import Mock

import pytest
from cognite.client import CogniteClient
from pydantic import BaseModel

from cognite_typed_functions.app import FunctionApp, create_function_service
from cognite_typed_functions.dependency_registry import DependencyRegistry
from cognite_typed_functions.models import ConfigurationError, FunctionCallInfo


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


class TestDependencyRegistryValidation:
    """Test validation and error handling in dependency registry."""

    def test_register_requires_target_type(self):
        """Test that target_type is mandatory - this is a typed functions framework."""
        registry = DependencyRegistry()

        class MyService:
            pass

        # target_type is mandatory, cannot be omitted
        # This test verifies that the type system enforces this at the function signature level
        # If someone tries to pass None, they'll get a type error
        # For runtime verification, we just check that valid registrations work
        registry.register(
            provider=lambda ctx: MyService(),
            target_type=MyService,
        )

        # Verify it's registered
        param = inspect.Parameter("service", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=MyService)
        assert registry.is_dependency("service", param)

    def test_register_with_only_type_succeeds(self):
        """Test that registering with only type works."""

        class MyService:
            pass

        registry = DependencyRegistry()

        # Should not raise - type-only registration (name is optional)
        registry.register(
            provider=lambda ctx: MyService(),
            target_type=MyService,
        )

        # Check that it's registered by verifying it matches a parameter with that type
        param = inspect.Parameter("my_param", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=MyService)
        assert registry.is_dependency("my_param", param)

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

    def test_register_blocked_type_str_raises_error(self):
        """Test that registering str as a dependency type is blocked."""
        registry = DependencyRegistry()

        with pytest.raises(ConfigurationError, match="type-only matching for generic type 'str'"):
            registry.register(
                provider=lambda ctx: "default",
                target_type=str,
            )

    def test_register_blocked_type_int_raises_error(self):
        """Test that registering int as a dependency type is blocked."""
        registry = DependencyRegistry()

        with pytest.raises(ConfigurationError, match="type-only matching for generic type 'int'"):
            registry.register(
                provider=lambda ctx: 42,
                target_type=int,
            )

    def test_register_blocked_type_dict_raises_error(self):
        """Test that registering bare dict as a dependency type is blocked."""
        registry = DependencyRegistry()

        with pytest.raises(ConfigurationError, match="type-only matching for generic type 'dict'"):
            registry.register(
                provider=lambda ctx: {},
                target_type=dict,
            )

    def test_register_blocked_type_list_raises_error(self):
        """Test that registering bare list as a dependency type is blocked."""
        registry = DependencyRegistry()

        with pytest.raises(ConfigurationError, match="type-only matching for generic type 'list'"):
            registry.register(
                provider=lambda ctx: [],
                target_type=list,
            )

    def test_register_blocked_type_object_raises_error(self):
        """Test that registering object as a dependency type is blocked."""
        registry = DependencyRegistry()

        with pytest.raises(ConfigurationError, match="type-only matching for generic type 'object'"):
            registry.register(
                provider=lambda ctx: object(),
                target_type=object,
            )

    def test_register_parameterized_dict_raises_error(self):
        """Test that registering parameterized dict[str, str] for type-only matching is blocked."""
        registry = DependencyRegistry()

        # Should fail - parameterized dict could conflict with request parameters
        with pytest.raises(ConfigurationError, match="type-only matching for generic type 'dict'"):
            registry.register(
                provider=lambda ctx: {"key": "value"},
                target_type=dict[str, str],
            )

    def test_register_parameterized_list_raises_error(self):
        """Test that registering parameterized list[int] for type-only matching is blocked."""
        registry = DependencyRegistry()

        # Should fail - parameterized list could conflict with query parameters like ?ids=1,2,3
        with pytest.raises(ConfigurationError, match="type-only matching for generic type 'list'"):
            registry.register(
                provider=lambda ctx: [1, 2, 3],
                target_type=list[int],
            )

    def test_register_bare_typing_list_raises_error(self):
        """Test that registering bare typing.List (without type args) is blocked."""
        registry = DependencyRegistry()

        # Should fail - typing.List without args is too generic
        with pytest.raises(ConfigurationError, match="type-only matching for generic type 'List'"):
            registry.register(
                provider=lambda ctx: [],
                target_type=List,  # noqa: UP006 - Testing deprecated type intentionally
            )

    def test_register_bare_typing_dict_raises_error(self):
        """Test that registering bare typing.Dict (without type args) is blocked."""
        registry = DependencyRegistry()

        # Should fail - typing.Dict without args is too generic
        with pytest.raises(ConfigurationError, match="type-only matching for generic type 'Dict'"):
            registry.register(
                provider=lambda ctx: {},
                target_type=Dict,  # noqa: UP006 - Testing deprecated type intentionally
            )

    def test_register_parameterized_typing_list_raises_error(self):
        """Test that registering parameterized typing.List[int] for type-only matching is blocked."""
        registry = DependencyRegistry()

        # Should fail - parameterized typing.List could conflict with request parameters
        with pytest.raises(ConfigurationError, match="type-only matching for generic type"):
            registry.register(
                provider=lambda ctx: [1, 2, 3],
                target_type=List[int],  # noqa: UP006 - Testing deprecated type intentionally
            )

    def test_register_parameterized_typing_dict_raises_error(self):
        """Test that registering parameterized typing.Dict[str, int] for type-only matching is blocked."""
        registry = DependencyRegistry()

        # Should fail - parameterized typing.Dict could conflict with request parameters
        with pytest.raises(ConfigurationError, match="type-only matching for generic type"):
            registry.register(
                provider=lambda ctx: {"key": 123},
                target_type=Dict[str, int],  # noqa: UP006 - Testing deprecated type intentionally
            )

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
        """Test that registering custom classes is allowed."""

        class CustomConfig:
            """Custom configuration class."""

            pass

        registry = DependencyRegistry()

        # Should not raise - custom classes are always allowed
        registry.register(
            provider=lambda ctx: CustomConfig(),
            target_type=CustomConfig,
        )

        # Verify it's registered with correct type (type-only, so param_name should be None)
        dep_infos = registry.registered_dependencies
        assert any(d.target_type == CustomConfig and d.param_name is None for d in dep_infos)

        param = inspect.Parameter("config", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=CustomConfig)
        assert registry.is_dependency("config", param)

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

    def test_blocked_types_error_message_is_helpful(self):
        """Test that the error message provides helpful guidance."""
        registry = DependencyRegistry()

        with pytest.raises(ConfigurationError) as exc_info:
            registry.register(
                provider=lambda ctx: 42,
                target_type=int,
            )

        error_message = str(exc_info.value)
        assert "too generic" in error_message
        assert "conflict with request parameters" in error_message
        assert "custom class" in error_message or "parameterized type" in error_message
        assert "param_name" in error_message

    def test_generic_abstract_type_requires_name(self):
        """Test that generic abstract types like Mapping require both name and type."""
        registry = DependencyRegistry()

        # Should fail - Mapping without name
        with pytest.raises(ConfigurationError) as exc_info:
            registry.register(
                provider=lambda ctx: {},
                target_type=Mapping,
            )

        error_message = str(exc_info.value)
        assert "Mapping" in error_message
        assert "type-only matching" in error_message
        assert "too generic" in error_message

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

    def test_duplicate_registration_type_only_raises_error(self):
        """Test that registering duplicate type-only dependency raises ConfigurationError."""
        registry = DependencyRegistry()

        class MyService:
            pass

        # First registration should succeed
        registry.register(
            provider=lambda ctx: MyService(),
            target_type=MyService,
        )

        # Second registration with same type should fail
        with pytest.raises(ConfigurationError) as exc_info:
            registry.register(
                provider=lambda ctx: MyService(),
                target_type=MyService,
            )

        error_message = str(exc_info.value)
        assert "already registered" in error_message
        assert "MyService" in error_message

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

    def test_type_only_does_not_conflict_with_name_and_type(self):
        """Test that type-only and name+type registrations don't conflict."""
        registry = DependencyRegistry()

        class Database:
            pass

        # Type-only registration
        registry.register(
            provider=lambda ctx: Database(),
            target_type=Database,
        )

        # Name+type registration with same type should succeed (different matching condition)
        registry.register(
            provider=lambda ctx: Database(),
            target_type=Database,
            param_name="primary_db",
        )

        # Both should be registered - check that we have 2 registrations, one type-only and one with name
        dep_infos = registry.registered_dependencies
        assert len(dep_infos) == 2
        # Both should have same target_type (Database), but different param_names
        assert any(d.param_name == "primary_db" and d.target_type == Database for d in dep_infos)
        assert any(d.param_name is None and d.target_type == Database for d in dep_infos)
