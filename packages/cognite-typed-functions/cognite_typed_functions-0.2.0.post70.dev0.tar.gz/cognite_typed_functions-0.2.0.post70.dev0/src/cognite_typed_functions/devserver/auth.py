"""Authentication utilities for creating CogniteClient from environment variables.

This module handles OAuth authentication with Microsoft Entra ID (formerly Azure AD)
for accessing Cognite Data Fusion.
"""

import logging

from cognite.client import ClientConfig, CogniteClient
from cognite.client.credentials import OAuthClientCredentials
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class AuthConfig(BaseSettings):
    """Authentication configuration for Cognite client.

    Configuration is automatically loaded from environment variables with the
    COGNITE_ prefix. For example, COGNITE_CLIENT_ID maps to the client_id field.
    """

    model_config = SettingsConfigDict(
        env_prefix="COGNITE_",
        case_sensitive=False,
        env_file_encoding="utf-8",
    )

    client_id: str
    client_secret: SecretStr
    tenant_id: str
    project: str
    base_url: str = "https://api.cognitedata.com"
    client_name: str = "typed-functions"
    token_url_base: str = "https://login.microsoftonline.com"


def get_cognite_client_from_env() -> CogniteClient:
    """Create a Cognite client from environment variables.

    Required environment variables:
        - COGNITE_CLIENT_ID: OAuth client ID
        - COGNITE_CLIENT_SECRET: OAuth client secret
        - COGNITE_TENANT_ID: Microsoft Entra ID tenant ID
        - COGNITE_PROJECT: Cognite project name

    Optional environment variables:
        - COGNITE_BASE_URL: Base URL for Cognite API (default: https://api.cognitedata.com)
        - COGNITE_CLIENT_NAME: Client name for tracking (default: typed-functions)
        - COGNITE_TOKEN_URL_BASE: Base URL for OAuth token endpoint
          (default: https://login.microsoftonline.com)
          Use this for Azure national clouds (e.g., Government, China)

    Returns:
        Authenticated CogniteClient instance

    Raises:
        ValidationError: If required environment variables are missing or invalid
        Exception: If client creation fails
    """
    try:
        # Pydantic Settings automatically loads and validates environment variables
        auth_config = AuthConfig()  # type: ignore[call-arg]  # BaseSettings loads from env vars
        client = get_cognite_client_from_auth_config(auth_config)
        logger.info("✅ Cognite client created successfully")
        return client
    except Exception as e:
        logger.error(f"❌ Failed to create Cognite client: {e!s}")
        raise


def get_cognite_client_from_auth_config(auth_config: AuthConfig) -> CogniteClient:
    """Get an authenticated Cognite client using OAuth client credentials.

    Args:
        auth_config: Authentication configuration with OAuth credentials

    Returns:
        Authenticated CogniteClient instance

    Raises:
        Exception: If authentication or client creation fails
    """
    logger.info(f"🔐 Creating Cognite client for project: {auth_config.project}, tenant: {auth_config.tenant_id}")
    logger.info(f"🔐 Client ID: {auth_config.client_id}")
    logger.info(f"🔐 Client Secret: {auth_config.client_secret}")  # SecretStr automatically redacts
    logger.info(f"🔐 Tenant ID: {auth_config.tenant_id}")
    logger.info(f"🔐 Project: {auth_config.project}")
    logger.info(f"🔐 Base URL: {auth_config.base_url}")
    logger.info(f"🔐 Client Name: {auth_config.client_name}")
    logger.info(f"🔐 Token URL Base: {auth_config.token_url_base}")

    creds = OAuthClientCredentials(
        token_url=f"{auth_config.token_url_base}/{auth_config.tenant_id}/oauth2/v2.0/token",
        client_id=auth_config.client_id,
        client_secret=auth_config.client_secret.get_secret_value(),
        scopes=[f"{auth_config.base_url}/.default"],
    )

    config = ClientConfig(
        client_name=auth_config.client_name,
        project=auth_config.project,
        credentials=creds,
        base_url=auth_config.base_url,
    )

    return CogniteClient(config)
