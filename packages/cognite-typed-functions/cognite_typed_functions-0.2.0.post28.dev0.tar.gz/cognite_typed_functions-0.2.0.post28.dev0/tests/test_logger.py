"""Tests for logger functionality and dependency injection.

These tests verify that:
1. Logger is properly isolated from other loggers
2. Logger can be dependency-injected into route handlers
3. Logger works with both sync and async handlers
4. Logger doesn't interfere with print statements or other logging
5. Logger supports different log levels
"""

import logging
import sys
from io import StringIO
from typing import cast
from unittest.mock import Mock

import pytest
from cognite.client import CogniteClient
from pydantic import BaseModel

from cognite_typed_functions import FunctionApp, create_function_service
from cognite_typed_functions.logger import (
    LOGGER_NAME,
    create_function_logger,
    get_function_logger,
)
from cognite_typed_functions.models import SecretsMapping


class ItemResponse(BaseModel):
    """Test response model."""

    id: int
    name: str
    logged: bool


class TestLoggerCreation:
    """Test logger creation and configuration."""

    def test_create_function_logger_default_level(self):
        """Test creating logger with default INFO level."""
        logger = create_function_logger()

        assert logger.name == LOGGER_NAME
        assert logger.level == logging.INFO
        assert logger.propagate is False
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)

    def test_create_function_logger_custom_level(self):
        """Test creating logger with custom DEBUG level."""
        logger = create_function_logger(logging.DEBUG)

        assert logger.level == logging.DEBUG
        assert logger.handlers[0].level == logging.DEBUG

    def test_get_function_logger(self):
        """Test getting the function logger instance."""
        # Clear any existing logger first
        existing_logger = logging.getLogger(LOGGER_NAME)
        existing_logger.handlers.clear()

        logger = get_function_logger()

        assert logger.name == LOGGER_NAME
        assert logger.propagate is False
        assert len(logger.handlers) >= 1

    def test_logger_isolation_no_propagation(self):
        """Test that logger doesn't propagate to root logger."""
        logger = create_function_logger()

        # Verify propagate is False
        assert logger.propagate is False

        # Verify it's a separate logger from root
        root_logger = logging.getLogger()
        assert logger is not root_logger
        assert logger.name != root_logger.name

    def test_logger_writes_to_stdout(self):
        """Test that logger writes to stdout (not stderr)."""
        logger = create_function_logger()

        assert len(logger.handlers) == 1
        handler = logger.handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        # Verify handler writes to stdout
        handler = cast(logging.StreamHandler[StringIO], handler)
        assert hasattr(handler, "stream")
        assert handler.stream is sys.stdout  # type: ignore[attr-defined]


class TestLoggerDependencyInjection:
    """Test logger dependency injection in route handlers."""

    @pytest.fixture
    def mock_client(self) -> CogniteClient:
        """Mock CogniteClient for testing."""
        return Mock(spec=CogniteClient)

    @pytest.fixture
    def app(self) -> FunctionApp:
        """Create test app."""
        return FunctionApp(title="Test App", version="1.0.0")

    def test_handler_with_logger(self, app: FunctionApp, mock_client: CogniteClient):
        """Test handler that declares logger parameter."""

        @app.get("/items/{item_id}")
        def get_item(client: CogniteClient, logger: logging.Logger, item_id: int) -> ItemResponse:
            """Handler with logger."""
            assert logger is not None
            assert isinstance(logger, logging.Logger)
            assert logger.name == LOGGER_NAME

            logger.info(f"Fetching item {item_id}")
            return ItemResponse(id=item_id, name="Test Item", logged=True)

        handle = create_function_service(app)

        result = handle(
            client=mock_client,
            data={
                "path": "/items/123",
                "method": "GET",
            },
        )

        assert isinstance(result, dict)
        assert result["success"] is True
        assert isinstance(result["data"], dict)
        assert result["data"]["id"] == 123
        assert result["data"]["logged"] is True

    def test_handler_without_logger(self, app: FunctionApp, mock_client: CogniteClient):
        """Test handler that doesn't declare logger parameter."""

        @app.get("/items/{item_id}")
        def get_item(client: CogniteClient, item_id: int) -> ItemResponse:
            """Handler without logger."""
            return ItemResponse(id=item_id, name="Test Item", logged=False)

        handle = create_function_service(app)

        result = handle(
            client=mock_client,
            data={
                "path": "/items/456",
                "method": "GET",
            },
        )

        assert isinstance(result, dict)
        assert result["success"] is True
        assert isinstance(result["data"], dict)
        assert result["data"]["id"] == 456
        assert result["data"]["logged"] is False

    def test_handler_with_logger_and_other_dependencies(self, app: FunctionApp, mock_client: CogniteClient):
        """Test handler with logger alongside other dependencies."""
        from cognite_typed_functions.models import FunctionCallInfo

        @app.get("/items/{item_id}")
        def get_item(
            client: CogniteClient,
            logger: logging.Logger,
            secrets: SecretsMapping,
            function_call_info: FunctionCallInfo,
            item_id: int,
        ) -> ItemResponse:
            """Handler with all dependencies."""
            assert client is not None
            assert logger is not None
            assert secrets is not None
            assert function_call_info is not None

            logger.info(f"Processing item {item_id}")
            return ItemResponse(id=item_id, name="Test Item", logged=True)

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
        assert result["success"] is True
        assert isinstance(result["data"], dict)
        assert result["data"]["logged"] is True

    def test_multiple_handlers_with_different_logger_usage(self, app: FunctionApp, mock_client: CogniteClient):
        """Test that different handlers can have different logger usage."""

        @app.get("/with-logger")
        def with_logger(client: CogniteClient, logger: logging.Logger) -> dict[str, bool]:
            """Handler with logger."""
            logger.info("This handler uses logger")
            return {"uses_logger": True}

        @app.get("/without-logger")
        def without_logger(client: CogniteClient) -> dict[str, bool]:
            """Handler without logger."""
            return {"uses_logger": False}

        handle = create_function_service(app)

        # Test with logger
        result1 = handle(client=mock_client, data={"path": "/with-logger", "method": "GET"})
        assert isinstance(result1, dict)
        assert isinstance(result1["data"], dict)
        assert result1["data"]["uses_logger"] is True

        # Test without logger
        result2 = handle(client=mock_client, data={"path": "/without-logger", "method": "GET"})
        assert isinstance(result2, dict)
        assert isinstance(result2["data"], dict)
        assert result2["data"]["uses_logger"] is False


class TestLoggerAsyncHandlers:
    """Test logger with async route handlers."""

    @pytest.fixture
    def mock_client(self) -> CogniteClient:
        """Mock CogniteClient for testing."""
        return Mock(spec=CogniteClient)

    @pytest.fixture
    def app(self) -> FunctionApp:
        """Create test app."""
        return FunctionApp(title="Test App", version="1.0.0")

    def test_async_handler_with_logger(self, app: FunctionApp, mock_client: CogniteClient):
        """Test async handler that uses logger."""

        @app.get("/items/{item_id}")
        async def get_item_async(client: CogniteClient, logger: logging.Logger, item_id: int) -> ItemResponse:
            """Async handler with logger."""
            assert logger is not None
            assert isinstance(logger, logging.Logger)

            logger.info(f"Async fetching item {item_id}")
            return ItemResponse(id=item_id, name="Async Item", logged=True)

        handle = create_function_service(app)

        result = handle(
            client=mock_client,
            data={
                "path": "/items/999",
                "method": "GET",
            },
        )

        assert isinstance(result, dict)
        assert result["success"] is True
        assert isinstance(result["data"], dict)
        assert result["data"]["id"] == 999
        assert result["data"]["logged"] is True


class TestLoggerIsolation:
    """Test that logger is isolated from other logging systems."""

    def test_logger_doesnt_affect_root_logger(self):
        """Test that our logger doesn't affect root logger."""
        # Get root logger
        root_logger = logging.getLogger()
        initial_root_handlers = len(root_logger.handlers)

        # Create our logger
        logger = create_function_logger()

        # Root logger should be unchanged
        assert len(root_logger.handlers) == initial_root_handlers
        assert logger not in root_logger.handlers

    def test_logger_doesnt_affect_other_loggers(self):
        """Test that our logger doesn't affect other named loggers."""
        # Create another logger
        other_logger = logging.getLogger("other.module")
        other_logger.setLevel(logging.WARNING)
        other_handler = logging.StreamHandler()
        other_logger.addHandler(other_handler)

        # Create our logger
        our_logger = create_function_logger(logging.DEBUG)

        # Other logger should be unchanged
        assert other_logger.level == logging.WARNING
        assert other_handler in other_logger.handlers
        assert our_logger is not other_logger

    def test_logger_isolation_with_propagate_false(self):
        """Test that propagate=False ensures complete isolation."""
        logger = create_function_logger()

        # Verify propagate is False
        assert logger.propagate is False

        # Even if root logger has handlers, our logger won't use them
        root_logger = logging.getLogger()

        # Our logger should only have its own handler
        assert len(logger.handlers) == 1
        assert logger.handlers[0] not in root_logger.handlers


class TestLoggerLevels:
    """Test logger with different log levels."""

    def test_logger_respects_log_levels(self):
        """Test that logger respects configured log levels."""
        # Create logger with INFO level
        logger = create_function_logger(logging.INFO)

        # Capture output
        output = StringIO()
        handler = logger.handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        handler.stream = output  # type: ignore[attr-defined]

        # Log at different levels
        logger.debug("This should not appear")
        logger.info("This should appear")
        logger.warning("This should also appear")

        output_str = output.getvalue()

        # DEBUG should not appear, INFO and WARNING should
        assert "This should not appear" not in output_str
        assert "This should appear" in output_str
        assert "This should also appear" in output_str

    def test_logger_debug_level(self):
        """Test logger with DEBUG level shows all messages."""
        logger = create_function_logger(logging.DEBUG)

        # Capture output
        output = StringIO()
        handler = logger.handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        handler.stream = output  # type: ignore[attr-defined]

        # Log at different levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        output_str = output.getvalue()

        # All messages should appear
        assert "Debug message" in output_str
        assert "Info message" in output_str
        assert "Warning message" in output_str
        assert "Error message" in output_str

    def test_logger_format(self):
        """Test logger output format."""
        logger = create_function_logger(logging.INFO)

        # Capture output
        output = StringIO()
        handler = logger.handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        handler.stream = output  # type: ignore[attr-defined]

        logger.info("Test message")

        output_str = output.getvalue()

        # Should contain timestamp, level, and message
        assert "[INFO]" in output_str
        assert "Test message" in output_str
        # Should have timestamp (just check for year format)
        assert "202" in output_str  # Year starts with 202x
