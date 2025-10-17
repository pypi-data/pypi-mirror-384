"""Development server module for local testing of Cognite Functions.

This module provides ASGI adapter functionality to run Cognite Typed Functions
locally using uvicorn or other ASGI servers.

Example:
    ```python
    from cognite_typed_functions.devserver import create_asgi_app
    from handler import handle

    app = create_asgi_app(handle)
    ```

    Then run with: `uv run uvicorn dev:app --reload`
"""

from .asgi import create_asgi_app
from .auth import AuthConfig, get_cognite_client_from_auth_config, get_cognite_client_from_env

__all__ = [
    "AuthConfig",
    "create_asgi_app",
    "get_cognite_client_from_auth_config",
    "get_cognite_client_from_env",
]
