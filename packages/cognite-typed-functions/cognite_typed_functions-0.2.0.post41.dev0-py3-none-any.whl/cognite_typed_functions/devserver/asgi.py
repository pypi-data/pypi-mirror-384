"""ASGI adapter for running Cognite Typed Functions locally with uvicorn.

This module provides the bridge between ASGI servers (like uvicorn) and the
Cognite Functions handle interface. It automatically detects and uses the
internal async implementation for optimal performance.
"""

import json
import logging
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

from cognite_typed_functions.models import DataDict, FunctionService

from .auth import get_cognite_client_from_env

logger = logging.getLogger(__name__)

# ASGI types
ASGIScope = dict[str, Any]
ASGIReceive = Callable[[], Awaitable[dict[str, Any]]]
ASGISend = Callable[[dict[str, Any]], Awaitable[None]]
ASGIApp = Callable[[ASGIScope, ASGIReceive, ASGISend], Awaitable[None]]


def asgi_error_handler(
    func: Callable[[ASGIScope, ASGIReceive, ASGISend], Awaitable[None]],
) -> Callable[[ASGIScope, ASGIReceive, ASGISend], Awaitable[None]]:
    """Decorator that handles errors at the ASGI transport layer.

    Most error handling is done in the centralized cognite_error_handler in app.py.
    This ASGI-level handler provides defense-in-depth by catching:
    - JSONDecodeError during request body parsing (before calling handle)
    - Any unexpected exceptions that escape the core error handler (safety net)

    Args:
        func: The async ASGI application function to wrap

    Returns:
        Wrapped async ASGI application with error handling
    """

    @wraps(func)
    async def wrapper(scope: ASGIScope, receive: ASGIReceive, send: ASGISend) -> None:
        try:
            await func(scope, receive, send)

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in request body: {e}")
            error_response = {
                "success": False,
                "error_type": "InvalidJSON",
                "message": f"Invalid JSON in request body: {e!s}",
            }
            await _send_json_response(send, error_response, status=400)

        except Exception as e:
            # Safety net: This should normally not be reached since cognite_error_handler
            # in app.py catches all exceptions. However, if there's a bug in the error
            # handling code itself or an unexpected framework-level exception, this ensures
            # we still return a proper error response instead of crashing.
            logger.exception("Unhandled exception in ASGI app (this should not happen)")
            error_response = {
                "success": False,
                "error_type": "ServerError",
                "message": "An internal server error occurred.",
                "details": {"exception_type": type(e).__name__},
            }
            await _send_json_response(send, error_response, status=500)

    return wrapper


def create_asgi_app(handle: FunctionService) -> ASGIApp:
    """Create an ASGI application from a Cognite Functions handle.

    This adapter uses the async implementation directly for optimal performance.
    Error handling for validation, conversion, and execution errors is centralized
    in the handle function itself, so this adapter only needs to handle JSON
    parsing errors during request parsing.

    Args:
        handle: The FunctionService instance created by create_function_service()

    Returns:
        ASGI application compatible with uvicorn, hypercorn, etc.

    Example:
        ```python
        from cognite_typed_functions import create_function_service
        from cognite_typed_functions.devserver import create_asgi_app

        handle = create_function_service(app)
        asgi_app = create_asgi_app(handle)
        ```

        Then run: `uv run uvicorn module:asgi_app --reload`
    """
    # Create Cognite client once at startup
    client = get_cognite_client_from_env()
    logger.info("🚀 ASGI app created successfully")
    logger.info("⚡ Using optimized async handle")

    @asgi_error_handler
    async def asgi_app(scope: ASGIScope, receive: ASGIReceive, send: ASGISend) -> None:
        """ASGI application entry point.

        Args:
            scope: ASGI connection scope with request metadata
            receive: ASGI receive callable for reading request body
            send: ASGI send callable for writing response
        """
        if scope["type"] != "http":
            # Only handle HTTP requests
            return

        # Parse the ASGI request into Cognite handle format
        # JSONDecodeError is caught by asgi_error_handler
        cognite_data = await _parse_asgi_request(scope, receive)

        # Call async handle - it returns error dicts instead of raising exceptions
        # All validation, conversion, and execution errors are handled inside
        result = await handle.async_handle(
            client=client,
            data=cognite_data,
            secrets=None,
            function_call_info=None,
        )

        # Send response (either success or error dict)
        await _send_json_response(send, result, status=200)

    return asgi_app


async def _parse_asgi_request(scope: ASGIScope, receive: ASGIReceive) -> DataDict:
    """Parse ASGI request into Cognite handle data format.

    Args:
        scope: ASGI connection scope
        receive: ASGI receive callable

    Returns:
        Data dict in Cognite handle format with path, method, and body
    """
    method = scope["method"]
    path = scope["path"]
    query_string = scope.get("query_string", b"").decode("utf-8")

    # Construct full path with query string
    full_path = path
    if query_string:
        full_path = f"{path}?{query_string}"

    # Read request body
    body_data: dict[str, Any] = {}
    if method in ("POST", "PUT", "PATCH"):
        body_bytes = await _read_body(receive)
        if body_bytes:
            try:
                body_data = json.loads(body_bytes.decode("utf-8"))
            except json.JSONDecodeError:
                # Let the caller handle the error
                raise

    # Return in Cognite handle format
    return {
        "path": full_path,
        "method": method,
        "body": body_data,
    }


async def _read_body(receive: ASGIReceive) -> bytes:
    """Read the complete request body from ASGI receive.

    Args:
        receive: ASGI receive callable

    Returns:
        Complete request body as bytes
    """
    body_parts: list[bytes] = []
    while True:
        message = await receive()
        if message["type"] == "http.request":
            body = message.get("body", b"")
            if body:
                body_parts.append(body)
            if not message.get("more_body", False):
                break
        elif message["type"] == "http.disconnect":
            # Client disconnected before sending the full body.
            break
    return b"".join(body_parts)


async def _send_json_response(send: ASGISend, data: Any, status: int = 200) -> None:
    """Send JSON response via ASGI send.

    Args:
        send: ASGI send callable
        data: Data to serialize as JSON
        status: HTTP status code
    """
    body = json.dumps(data).encode("utf-8")

    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                [b"content-type", b"application/json"],
                [b"content-length", str(len(body)).encode("utf-8")],
            ],
        }
    )

    await send(
        {
            "type": "http.response.body",
            "body": body,
        }
    )
