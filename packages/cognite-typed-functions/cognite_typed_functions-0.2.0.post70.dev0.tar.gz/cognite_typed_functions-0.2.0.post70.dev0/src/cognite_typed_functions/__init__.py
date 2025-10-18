"""Typed Cognite Functions.

Enterprise framework for building composable, type-safe Cognite Functions
with automatic validation, built-in introspection, and AI integration.
"""

from ._version import __version__
from .app import FunctionApp, create_function_service
from .dependency_registry import (
    DependencyContext,
    DependencyInfo,
    DependencyRegistry,
    ProviderFunction,
    create_default_registry,
    resolve_dependencies,
)
from .introspection import create_introspection_app
from .logger import create_function_logger, get_function_logger
from .mcp import MCPApp, create_mcp_app
from .models import (
    CogniteTypedError,
    CogniteTypedFunctionsError,
    CogniteTypedResponse,
    ConfigurationError,
    FunctionService,
    HTTPMethod,
    SecretsMapping,
)
from .routing import Router, SortedRoutes, find_matching_route

__all__ = [
    "CogniteTypedError",
    "CogniteTypedFunctionsError",
    "CogniteTypedResponse",
    "ConfigurationError",
    "DependencyContext",
    "DependencyInfo",
    "DependencyRegistry",
    "FunctionApp",
    "FunctionService",
    "HTTPMethod",
    "MCPApp",
    "ProviderFunction",
    "Router",
    "SecretsMapping",
    "SortedRoutes",
    "__version__",
    "create_default_registry",
    "create_function_logger",
    "create_function_service",
    "create_introspection_app",
    "create_mcp_app",
    "find_matching_route",
    "get_function_logger",
    "resolve_dependencies",
]
