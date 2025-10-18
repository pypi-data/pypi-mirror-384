"""Isolated logger for Cognite Functions with dependency injection support.

This module provides an enterprise-grade logging solution that works across
all cloud providers (AWS Lambda, Azure Functions, GCP Cloud Run) by writing
directly to stdout while remaining completely isolated from other logging
systems.

Key Features:
    - Standard Python logging API (logger.info, logger.warning, logger.error, etc.)
    - Writes to stdout (captured by all cloud providers)
    - Completely isolated from other loggers (no interference with wrapper code)
    - Dependency injection support (inject via function signature)
    - Configurable log levels per function call

Background:
    Cognite Functions documentation states that the logging module is not
    recommended because it can interfere with their logging infrastructure.
    This implementation avoids those issues by:
    - Using a named logger with propagate=False (no root logger interference)
    - Writing only to stdout (same as print statements)
    - Not capturing or redirecting other logging/print statements

Example usage:
    ```python
    from cognite_typed_functions import FunctionApp
    from logging import Logger

    app = FunctionApp("My Function", "1.0.0")

    @app.get("/items/{item_id}")
    def get_item(client, logger: Logger, item_id: int) -> dict:
        logger.info(f"Fetching item {item_id}")
        # Your logic here
        logger.debug(f"Item details: {item}")
        return {"id": item_id, "name": "Widget"}
    ```

The logger is automatically configured and injected when your function
declares a `logger` parameter with type `logging.Logger`.
"""

import logging
import sys
from logging import Logger

# Logger name for all user functions
LOGGER_NAME = "cognite_typed_functions.user"

# Default log level
DEFAULT_LOG_LEVEL = logging.INFO


def create_function_logger(level: int = DEFAULT_LOG_LEVEL) -> Logger:
    """Create an isolated logger for Cognite Functions.

    This logger writes to stdout and is completely isolated from other
    loggers in the system. It will not interfere with wrapper code or
    other logging systems.

    Args:
        level: The logging level (e.g., logging.INFO, logging.DEBUG).
               Defaults to INFO.

    Returns:
        A configured Logger instance that writes to stdout.

    Example:
        ```python
        logger = create_function_logger(logging.DEBUG)
        logger.info("Processing started")
        logger.debug("Detailed debug information")
        logger.warning("Something unexpected happened")
        logger.error("An error occurred")
        ```
    """
    # Get or create the named logger
    logger = logging.getLogger(LOGGER_NAME)

    # Clear any existing handlers to ensure clean state
    logger.handlers.clear()

    # Set the log level
    logger.setLevel(level)

    # Critical: Don't propagate to root logger or parent loggers
    # This ensures complete isolation from other logging systems
    logger.propagate = False

    # Create stdout handler (same as print statements)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    # Use a clean, professional format
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    return logger


def get_function_logger() -> Logger:
    """Get the function logger instance.

    This is a convenience function that returns the logger with default
    settings. If you need a different log level, use create_function_logger()
    directly.

    Returns:
        The configured Logger instance.
    """
    # Check if logger already exists and is configured
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return logger

    # Create new logger with default settings
    return create_function_logger()


__all__ = [
    "DEFAULT_LOG_LEVEL",
    "LOGGER_NAME",
    "create_function_logger",
    "get_function_logger",
]
