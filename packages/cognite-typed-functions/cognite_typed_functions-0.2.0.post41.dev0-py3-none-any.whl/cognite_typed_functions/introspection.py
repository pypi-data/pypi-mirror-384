"""Core introspection endpoints as a composable app.

This module provides introspection capabilities as a separate FunctionApp that can be
composed with other apps. The introspection app provides endpoints for discovering,
debugging, and monitoring Cognite Functions applications at runtime.

Key Features:
    - Clean separation: Introspection is its own FunctionApp using standard decorators
    - Composed route access: Can introspect routes from all composed apps
    - Standard composition: Works with create_function_service(introspection_app, app)
    - Optional inclusion: Users can choose whether to include introspection endpoints

Example Usage:
    ```python
    from cognite_typed_functions import FunctionApp, create_function_service
    from cognite_typed_functions.introspection import create_introspection_app

    # Create apps
    introspection_app = create_introspection_app()
    app = FunctionApp("My API", "1.0.0")

    @app.get("/items/{item_id}")
    def get_item(client: CogniteClient, item_id: int) -> dict:
        return {"id": item_id, "name": "Widget"}

    # Compose apps - put introspection first to see all other apps
    handle = create_function_service(introspection_app, app)

    # Available endpoints:
    # GET /__schema__ -> OpenAPI schema including /items/{item_id}
    # GET /__routes__ -> List of all routes from all apps
    # GET /__health__ -> Health status and statistics
    # GET /__ping__ -> Connectivity check
    ```

Introspection Endpoints:
    /__schema__ (GET): Returns OpenAPI-compatible schema describing all routes and data models
    /__routes__ (GET): Lists all registered routes with their methods and descriptions
    /__health__ (GET): Provides application health status and basic metrics
    /__ping__ (GET): Simple connectivity check endpoint (useful for MCP and monitoring)

Architecture:
    1. Introspection app handles /__* routes using standard decorators
    2. Overrides set_composition_context() to receive composition context
    3. Generates schemas and route information for all apps in composition
    4. Works seamlessly with MCP and main apps in composed applications
"""

from collections.abc import Mapping, Sequence
from typing import Any

from cognite.client import CogniteClient

from ._version import __version__
from .app import FunctionApp
from .models import HTTPMethod
from .routing import RouteInfo
from .schema import SchemaGenerator


class IntrospectionApp(FunctionApp):
    """Introspection app that provides system endpoints.

    This app should be placed first in the composition order to see all other apps.
    """

    def __init__(self) -> None:
        """Initialize the introspection app."""
        super().__init__("Introspection", __version__)

        # Initialize with fallback values for standalone usage
        self.app_list: list[FunctionApp] = [self]
        self.all_routes: dict[str, Mapping[HTTPMethod, RouteInfo]] = dict(self.routes)
        self.main_app: FunctionApp = self

    def set_context(self, routes: Mapping[str, Mapping[HTTPMethod, RouteInfo]], apps: Sequence[FunctionApp]) -> None:
        """Override to compute app list and routes from composition context."""
        # Include introspection app and routes in addition to downstream
        self.app_list = [self, *apps]
        self.all_routes = {**routes, **self.routes}

        # Always use the last app (main business app) for main app info
        self.main_app = self.app_list[-1] if self.app_list else self


def create_introspection_app() -> IntrospectionApp:
    """Create an introspection app that provides system endpoints.

    Returns:
        IntrospectionApp configured with introspection endpoints
    """
    introspection_app = IntrospectionApp()

    @introspection_app.get("/__schema__")
    def get_schema(client: CogniteClient) -> dict[str, Any]:
        """Get OpenAPI schema for all routes in the composed application."""
        title = introspection_app.main_app.title
        version = introspection_app.main_app.version

        return SchemaGenerator.generate_openapi_schema(
            title=title,
            version=version,
            routes={path: dict(methods) for path, methods in introspection_app.all_routes.items()},
        )

    @introspection_app.get("/__routes__")
    def get_routes(client: CogniteClient) -> dict[str, Any]:
        """Get information about all registered routes."""
        routes_info = {}
        for route_path, methods in introspection_app.all_routes.items():
            routes_info[route_path] = {
                "methods": [str(method) for method in methods.keys()],
                "descriptions": {str(method): info.description for method, info in methods.items()},
            }

        app_info = {
            "title": introspection_app.main_app.title,
            "version": introspection_app.main_app.version,
            "total_apps": len(introspection_app.app_list),
            "app_names": [app.title for app in introspection_app.app_list],
        }

        return {
            "app_info": app_info,
            "routes": routes_info,
        }

    @introspection_app.get("/__health__")
    def get_health(client: CogniteClient) -> dict[str, Any]:
        """Get application health status and statistics."""
        # Calculate statistics
        total_routes = sum(len(methods) for methods in introspection_app.all_routes.values())
        route_count_by_method: dict[str, int] = {}
        for methods in introspection_app.all_routes.values():
            for method in methods.keys():
                method_str = str(method)
                route_count_by_method[method_str] = route_count_by_method.get(method_str, 0) + 1

        return {
            "status": "healthy",
            "app": introspection_app.main_app.title,
            "version": introspection_app.main_app.version,
            "composed_apps": [{"name": app.title, "routes": len(app.routes)} for app in introspection_app.app_list],
            "statistics": {
                "total_routes": total_routes,
                "total_apps": len(introspection_app.app_list),
                "routes_by_method": route_count_by_method,
            },
        }

    @introspection_app.get("/__ping__")
    def ping(client: CogniteClient) -> dict[str, Any]:
        """Simple connectivity check endpoint."""
        # Empty response for MCP and monitoring tools
        return {}

    return introspection_app
