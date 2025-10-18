"""OpenAPI schema generation for Cognite typed functions.

This module provides the SchemaGenerator class responsible for generating
OpenAPI 3.1 compliant schemas from function metadata. It handles:

- Converting Python types to OpenAPI type specifications
- Generating comprehensive API documentation schemas
- Processing path parameters, query parameters, and request bodies
- Creating response schemas with proper error handling definitions

OpenAPI 3.1 is fully compatible with JSON Schema Draft 2020-12, which means
Pydantic-generated schemas work almost natively with minimal cleanup!

The generated schemas are used for documentation and validation purposes
in the Cognite Functions platform.
"""

import copy
import inspect
import re
from typing import Any, cast

from pydantic import BaseModel

from .dependency_registry import DependencyRegistry
from .models import CogniteTypedError, CogniteTypedResponse, HTTPMethod
from .routing import RouteInfo


class SchemaGenerator:
    """Handles OpenAPI 3.1 schema generation for Cognite Functions."""

    @staticmethod
    def _clean_pydantic_schema_for_openapi(pydantic_schema: dict[str, Any]) -> dict[str, Any]:
        """Clean Pydantic-generated JSON schema to be OpenAPI 3.1 compliant.

        OpenAPI 3.1 is fully compatible with JSON Schema Draft 2020-12, but we need to
        ensure $ref paths work correctly within component schemas. This method inlines
        simple $defs to avoid reference resolution issues.

        Args:
            pydantic_schema: Raw schema from Pydantic's model_json_schema()

        Returns:
            OpenAPI 3.1 compliant schema with inlined definitions
        """
        cleaned_schema = copy.deepcopy(pydantic_schema)

        # Remove title if redundant in component schema context
        cleaned_schema.pop("title", None)

        # Inline simple $defs to avoid reference resolution issues
        defs = cleaned_schema.pop("$defs", {})
        if defs:
            SchemaGenerator._inline_simple_refs(cleaned_schema, defs)

        return cleaned_schema

    @staticmethod
    def _inline_simple_refs(schema: Any, defs: dict[str, Any], visited: set[str] | None = None) -> None:
        """Recursively inline simple $ref references with their definitions.

        This method safely handles nested references and circular dependencies by:
        1. Tracking visited definitions to prevent infinite recursion
        2. Deep copying definitions before inlining to avoid mutation issues
        3. Recursively processing inlined content for nested references
        """
        if visited is None:
            visited = set()

        if isinstance(schema, dict):
            schema = cast(dict[str, Any], schema)
            ref = schema.get("$ref")
            if ref:
                # Use regex patterns to extract definition names from different $ref formats
                def_name = SchemaGenerator._extract_ref_name(ref)

                if def_name and def_name in defs:
                    # Check for circular reference
                    if def_name in visited:
                        # Replace circular reference with generic object to break the cycle
                        schema.clear()
                        schema.update({"type": "object", "description": f"Circular reference to {def_name}"})
                        return

                    # Add to visited set and make a deep copy of the definition
                    visited.add(def_name)
                    definition = copy.deepcopy(defs[def_name])

                    # Recursively process the definition to handle nested references
                    SchemaGenerator._inline_simple_refs(definition, defs, visited)

                    # Replace the $ref with the processed definition
                    schema.clear()
                    schema.update(definition)

                    # Remove from visited set after processing
                    visited.discard(def_name)
                elif SchemaGenerator._is_basemodel_ref(ref):
                    # Handle BaseModel references - replace with generic object
                    schema.clear()
                    schema.update({"type": "object", "description": "Base model object"})
            else:
                # Recursively process nested objects
                for value in schema.values():
                    SchemaGenerator._inline_simple_refs(value, defs, visited)
        elif isinstance(schema, list):
            schema = cast(list[Any], schema)
            for item in schema:
                SchemaGenerator._inline_simple_refs(item, defs, visited)

    @staticmethod
    def _extract_ref_name(ref: str) -> str | None:
        """Extract definition name from $ref string using regex patterns.

        Supports both JSON Schema ($defs) and OpenAPI (components/schemas) formats.

        Examples:
            "#/$defs/MyModel" -> "MyModel"
            "#/components/schemas/MyModel" -> "MyModel"
            "invalid/ref" -> None
        """
        # Pattern for JSON Schema $defs format: #/$defs/ModelName
        defs_pattern = r"^#/\$defs/(.+)$"

        # Pattern for OpenAPI components format: #/components/schemas/ModelName
        components_pattern = r"^#/components/schemas/(.+)$"

        for pattern in [defs_pattern, components_pattern]:
            match = re.match(pattern, ref)
            if match:
                return match.group(1)

        return None

    @staticmethod
    def _is_basemodel_ref(ref: str) -> bool:
        """Check if $ref points to BaseModel using regex pattern."""
        basemodel_pattern = r"^#/(?:\$defs|components/schemas)/BaseModel$"
        return bool(re.match(basemodel_pattern, ref))

    @staticmethod
    def _handle_list_type_schema(
        return_type: type[Any], component_schemas: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """Generate OpenAPI schema for list types."""
        args = getattr(return_type, "__args__", ())
        if not args:
            return {"type": "array", "items": {"type": "object"}}

        item_type = args[0]

        # Handle Pydantic models
        if inspect.isclass(item_type) and issubclass(item_type, BaseModel):
            model_name = item_type.__name__
            if model_name not in component_schemas:
                model_schema = item_type.model_json_schema(by_alias=True, ref_template="#/components/schemas/{model}")
                component_schemas[model_name] = SchemaGenerator._clean_pydantic_schema_for_openapi(model_schema)
            return {"type": "array", "items": {"$ref": f"#/components/schemas/{model_name}"}}

        # Handle basic types
        item_schema = {"type": SchemaGenerator._python_type_to_openapi(item_type)}
        return {"type": "array", "items": item_schema}

    @staticmethod
    def _python_type_to_openapi(python_type: type[Any]) -> str:
        """Convert Python type to OpenAPI type string."""
        match python_type:
            case x if x is int:
                return "integer"
            case x if x is float:
                return "number"
            case x if x is bool:
                return "boolean"
            case x if x is str:
                return "string"
            case x if x is dict:
                return "object"
            case x if x is list:
                return "array"
            case _ if hasattr(python_type, "__origin__") and getattr(python_type, "__origin__", None) is list:
                return "array"
            case _ if hasattr(python_type, "__origin__") and getattr(python_type, "__origin__", None) is dict:
                return "object"
            case _:
                return "string"  # Default fallback

    @staticmethod
    def _generate_response_schema(
        route_info: RouteInfo, component_schemas: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """Generate response schema from function return type hint."""
        return_type = route_info.type_hints.get("return")

        if return_type is None:
            # No return type hint, use generic object
            return {"type": "object"}

        # Check if it's a Pydantic model
        if inspect.isclass(return_type) and issubclass(return_type, BaseModel):
            # Generate schema for Pydantic model and add to components
            model_name = return_type.__name__
            if model_name not in component_schemas:
                model_schema = return_type.model_json_schema(by_alias=True, ref_template="#/components/schemas/{model}")
                component_schemas[model_name] = SchemaGenerator._clean_pydantic_schema_for_openapi(model_schema)

            # Return reference to the component schema
            return {"$ref": f"#/components/schemas/{model_name}"}

        # Handle basic Python types
        if return_type in (int, float, bool, str):
            return {"type": SchemaGenerator._python_type_to_openapi(return_type)}

        # Handle lists
        if hasattr(return_type, "__origin__") and getattr(return_type, "__origin__", None) is list:
            return SchemaGenerator._handle_list_type_schema(return_type, component_schemas)

        # Handle dictionaries
        if hasattr(return_type, "__origin__") and getattr(return_type, "__origin__", None) is dict:
            return {"type": "object"}

        # Default fallback
        return {"type": "object"}

    @staticmethod
    def _generate_request_body_schema(
        pydantic_models: list[tuple[str, type[BaseModel]]], component_schemas: dict[str, dict[str, Any]]
    ) -> dict[str, Any] | None:
        """Generate request body schema from Pydantic models."""
        if not pydantic_models:
            return None

        if len(pydantic_models) == 1:
            # Single Pydantic model - reference it directly
            param_name, model_type = pydantic_models[0]
            model_name = model_type.__name__

            if model_name not in component_schemas:
                model_schema = model_type.model_json_schema(by_alias=True, ref_template="#/components/schemas/{model}")
                component_schemas[model_name] = SchemaGenerator._clean_pydantic_schema_for_openapi(model_schema)

            return {"$ref": f"#/components/schemas/{model_name}"}

        # Multiple Pydantic models - create object with each as a property
        properties: dict[str, dict[str, str]] = {}
        required: list[str] = []

        for param_name, model_type in pydantic_models:
            model_name = model_type.__name__

            if model_name not in component_schemas:
                model_schema = model_type.model_json_schema(by_alias=True, ref_template="#/components/schemas/{model}")
                component_schemas[model_name] = SchemaGenerator._clean_pydantic_schema_for_openapi(model_schema)

            properties[param_name] = {"$ref": f"#/components/schemas/{model_name}"}
            required.append(param_name)

        return {"type": "object", "properties": properties, "required": required}

    @staticmethod
    def _add_path_parameters(
        operation: dict[str, Any], route_info: RouteInfo, dependency_param_names: frozenset[str]
    ) -> None:
        """Add path parameters to the OpenAPI operation.

        Args:
            operation: OpenAPI operation object to add parameters to
            route_info: Route information containing parameters
            dependency_param_names: Names of dependency parameters to exclude from schema
        """
        for param_name in route_info.path_params:
            # Skip dependency injection parameters
            if param_name in dependency_param_names:
                continue
            if param_name in route_info.parameters:
                param_type = route_info.type_hints.get(param_name, str)
                operation["parameters"].append(
                    {
                        "name": param_name,
                        "in": "path",
                        "required": True,
                        "description": f"Path parameter {param_name}",
                        "schema": {"type": SchemaGenerator._python_type_to_openapi(param_type)},
                    }
                )

    @staticmethod
    def _add_query_parameters_and_collect_pydantic_models(
        operation: dict[str, Any], route_info: RouteInfo, dependency_param_names: frozenset[str]
    ) -> list[tuple[str, type[BaseModel]]]:
        """Add query parameters to operation and collect Pydantic models for request body.

        Args:
            operation: OpenAPI operation object to add parameters to
            route_info: Route information containing parameters
            dependency_param_names: Names of dependency parameters to exclude from schema

        Returns:
            List of (param_name, model_type) tuples for Pydantic models to include in request body
        """
        pydantic_models_list: list[tuple[str, type[BaseModel]]] = []
        for param_name, param_info in route_info.parameters.items():
            # Skip dependency injection parameters
            if param_name in dependency_param_names:
                continue
            if param_name not in route_info.path_params:
                param_type = route_info.type_hints.get(param_name, str)
                # Check if it's a Pydantic model
                if inspect.isclass(param_type) and issubclass(param_type, BaseModel):
                    # Create tuple with explicit typing to help type checker
                    pydantic_models_list.append((param_name, param_type))
                else:
                    operation["parameters"].append(
                        {
                            "name": param_name,
                            "in": "query",
                            "required": param_info.default == inspect.Parameter.empty,
                            "description": f"Query parameter {param_name}",
                            "schema": {"type": SchemaGenerator._python_type_to_openapi(param_type)},
                        }
                    )
        return pydantic_models_list

    @staticmethod
    def _add_request_body_if_needed(
        operation: dict[str, Any],
        method: HTTPMethod,
        pydantic_models_list: list[tuple[str, type[BaseModel]]],
        component_schemas: dict[str, dict[str, Any]],
    ) -> None:
        """Add request body to operation for methods that support it."""
        if method in [HTTPMethod.POST, HTTPMethod.PUT] and pydantic_models_list:
            request_body_schema = SchemaGenerator._generate_request_body_schema(
                pydantic_models_list,
                component_schemas,
            )
            if request_body_schema:
                operation["requestBody"] = {
                    "required": True,
                    "content": {"application/json": {"schema": request_body_schema}},
                }

    @staticmethod
    def _generate_component_schemas(component_schemas: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Generate component schemas section for OpenAPI."""
        base_schemas = {
            "CogniteTypedError": SchemaGenerator._clean_pydantic_schema_for_openapi(
                CogniteTypedError.model_json_schema(
                    by_alias=True,  # Use field aliases if defined
                    ref_template="#/components/schemas/{model}",  # OpenAPI-style refs
                )
            ),
            "CogniteTypedResponse": SchemaGenerator._clean_pydantic_schema_for_openapi(
                CogniteTypedResponse.model_json_schema(
                    by_alias=True,  # Use field aliases if defined
                    ref_template="#/components/schemas/{model}",  # OpenAPI-style refs
                )
            ),
        }

        # Merge with collected component schemas. We intentionally put the base schemas last to avoid overriding the
        # component schemas, e.g so users cannot redefine the base schemas like CogniteTypedError and
        # CogniteTypedResponse.
        return {**component_schemas, **base_schemas}

    @staticmethod
    def _create_operation_object(route_info: RouteInfo, response_schema: dict[str, Any]) -> dict[str, Any]:
        """Create the base operation object for OpenAPI path item."""
        return {
            "summary": route_info.description.split("\n")[0],  # First line as summary
            "description": route_info.description,
            "parameters": [],
            "responses": {
                "200": {
                    "description": "Success",
                    "content": {"application/json": {"schema": response_schema}},
                },
                "400": {
                    "description": "Validation Error",
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/CogniteTypedError"}}},
                },
            },
        }

    @staticmethod
    def generate_openapi_schema(
        title: str,
        version: str,
        routes: dict[str, dict[HTTPMethod, RouteInfo]],
        registry: DependencyRegistry,
    ) -> dict[str, Any]:
        """Generate comprehensive OpenAPI 3.1 schema for documentation.

        OpenAPI 3.1 brings full JSON Schema compatibility, making this much simpler
        than previous versions that required complex transformations.

        Args:
            title: API title
            version: API version
            routes: Routes to include in the schema
            registry: Dependency registry to filter out dependency parameters from schema

        Returns:
            OpenAPI 3.1 compliant schema dictionary
        """
        schema: dict[str, Any] = {
            "openapi": "3.1.0",
            "info": {
                "title": title,
                "version": version,
                "description": f"Auto-generated API documentation for {title}",
            },
            "servers": [{"url": "/", "description": "Cognite Function"}],
            "paths": {},
        }

        # Track schemas to add to components section
        component_schemas: dict[str, dict[str, Any]] = {}

        for path, methods in routes.items():
            schema["paths"][path] = {}
            for method, route_info in methods.items():
                # Get dependency parameter names for filtering
                dependency_param_names = registry.get_dependency_param_names(route_info.signature)

                # Generate response schema from return type
                response_schema = SchemaGenerator._generate_response_schema(route_info, component_schemas)

                # Create base operation object
                operation = SchemaGenerator._create_operation_object(route_info, response_schema)

                # Add path parameters (excluding dependencies)
                SchemaGenerator._add_path_parameters(operation, route_info, dependency_param_names)

                # Add query parameters and collect Pydantic models for request body (excluding dependencies)
                pydantic_models_list = SchemaGenerator._add_query_parameters_and_collect_pydantic_models(
                    operation, route_info, dependency_param_names
                )

                # Add request body for methods that support it
                SchemaGenerator._add_request_body_if_needed(operation, method, pydantic_models_list, component_schemas)

                schema["paths"][path][method.lower()] = operation

        # Add component schemas - now with full JSON Schema support in OpenAPI 3.1!
        all_schemas = SchemaGenerator._generate_component_schemas(component_schemas)
        schema["components"] = {"schemas": all_schemas}

        return schema
