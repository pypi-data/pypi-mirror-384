"""Tests for OpenAPI schema generation functionality.

This module tests the SchemaGenerator class, particularly focusing on the
_inline_simple_refs method improvements for handling nested and circular references.
"""

import copy
import inspect
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

from cognite_typed_functions.models import HTTPMethod
from cognite_typed_functions.routing import RouteInfo
from cognite_typed_functions.schema import SchemaGenerator


class SimpleModel(BaseModel):
    """Simple model for basic testing."""

    name: str
    value: int


class NestedModel(BaseModel):
    """Model that references another model."""

    title: str
    simple: SimpleModel


class CircularModelA(BaseModel):
    """Model that creates circular reference with CircularModelB."""

    name: str
    b_ref: "CircularModelB | None" = None


class CircularModelB(BaseModel):
    """Model that creates circular reference with CircularModelA."""

    description: str
    a_ref: CircularModelA | None = None


class DeeplyNestedModel(BaseModel):
    """Model with multiple levels of nesting."""

    level1: NestedModel
    items: list[SimpleModel]


class TestSchemaGenerator:
    """Test the SchemaGenerator class functionality."""

    def test_clean_pydantic_schema_basic(self):
        """Test basic schema cleaning functionality."""
        # Create a simple Pydantic schema
        schema = SimpleModel.model_json_schema()

        # Clean it
        cleaned = SchemaGenerator._clean_pydantic_schema_for_openapi(schema)  # type: ignore[reportPrivateUsage]

        # Should remove title and handle any $defs
        assert "title" not in cleaned
        assert cleaned["type"] == "object"
        assert "properties" in cleaned

    def test_inline_simple_refs_no_defs(self):
        """Test _inline_simple_refs with schema containing no references."""
        schema = {"type": "object", "properties": {"name": {"type": "string"}, "value": {"type": "integer"}}}
        original_schema = copy.deepcopy(schema)

        # Should not modify schema without $defs
        SchemaGenerator._inline_simple_refs(schema, {})  # type: ignore[reportPrivateUsage]

        assert schema == original_schema

    def test_inline_simple_refs_basic_reference(self):
        """Test _inline_simple_refs with basic reference resolution."""
        defs = {
            "SimpleModel": {"type": "object", "properties": {"name": {"type": "string"}, "value": {"type": "integer"}}}
        }

        schema: Any = {"type": "object", "properties": {"model": {"$ref": "#/$defs/SimpleModel"}}}

        SchemaGenerator._inline_simple_refs(schema, defs)  # type: ignore[reportPrivateUsage]

        # Reference should be inlined
        assert "$ref" not in schema["properties"]["model"]
        assert schema["properties"]["model"]["type"] == "object"
        assert "name" in schema["properties"]["model"]["properties"]
        assert "value" in schema["properties"]["model"]["properties"]

    def test_inline_simple_refs_nested_references(self):
        """Test _inline_simple_refs with nested references."""
        defs = {
            "SimpleModel": {"type": "object", "properties": {"name": {"type": "string"}, "value": {"type": "integer"}}},
            "NestedModel": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "simple": {"$ref": "#/$defs/SimpleModel"},  # Nested reference
                },
            },
        }

        schema: Any = {"type": "object", "properties": {"nested": {"$ref": "#/$defs/NestedModel"}}}

        SchemaGenerator._inline_simple_refs(schema, defs)  # type: ignore[reportPrivateUsage]

        # Both references should be resolved
        nested_prop = schema["properties"]["nested"]
        assert "$ref" not in nested_prop
        assert nested_prop["type"] == "object"

        # Nested reference should also be resolved
        simple_prop = nested_prop["properties"]["simple"]
        assert "$ref" not in simple_prop
        assert simple_prop["type"] == "object"
        assert "name" in simple_prop["properties"]

    def test_inline_simple_refs_circular_references(self):
        """Test _inline_simple_refs handles circular references safely."""
        defs: Any = {
            "CircularA": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "b_ref": {"$ref": "#/$defs/CircularB"}},
            },
            "CircularB": {
                "type": "object",
                "properties": {"description": {"type": "string"}, "a_ref": {"$ref": "#/$defs/CircularA"}},
            },
        }

        schema: Any = {"type": "object", "properties": {"circular": {"$ref": "#/$defs/CircularA"}}}

        # Should not raise RecursionError or infinite loop
        SchemaGenerator._inline_simple_refs(schema, defs)  # type: ignore[reportPrivateUsage]

        # Should have broken circular reference with generic object
        circular_prop = schema["properties"]["circular"]
        assert circular_prop["type"] == "object"

        # One of the circular references should be broken
        b_ref = circular_prop["properties"]["b_ref"]
        if "$ref" not in b_ref:
            # If b_ref was inlined, check that circular reference was broken
            if "a_ref" in b_ref.get("properties", {}):
                a_ref = b_ref["properties"]["a_ref"]
                assert "Circular reference" in a_ref.get("description", "")

    def test_inline_simple_refs_array_with_references(self):
        """Test _inline_simple_refs with references inside arrays."""
        defs: Any = {
            "ItemModel": {"type": "object", "properties": {"id": {"type": "integer"}, "name": {"type": "string"}}}
        }

        schema: Any = {"type": "array", "items": {"$ref": "#/$defs/ItemModel"}}

        SchemaGenerator._inline_simple_refs(schema, defs)  # type: ignore[reportPrivateUsage]

        # Reference in array items should be resolved
        assert "$ref" not in schema["items"]
        assert schema["items"]["type"] == "object"
        assert "id" in schema["items"]["properties"]

    def test_inline_simple_refs_multiple_same_reference(self):
        """Test _inline_simple_refs with multiple instances of same reference."""
        defs: Any = {"SharedModel": {"type": "object", "properties": {"shared_field": {"type": "string"}}}}

        schema: Any = {
            "type": "object",
            "properties": {
                "first": {"$ref": "#/$defs/SharedModel"},
                "second": {"$ref": "#/$defs/SharedModel"},
                "third": {"type": "array", "items": {"$ref": "#/$defs/SharedModel"}},
            },
        }

        SchemaGenerator._inline_simple_refs(schema, defs)  # type: ignore[reportPrivateUsage]

        # All references should be resolved
        for prop_name in ["first", "second"]:
            prop = schema["properties"][prop_name]
            assert "$ref" not in prop
            assert prop["type"] == "object"
            assert "shared_field" in prop["properties"]

        # Array item reference should also be resolved
        third_items = schema["properties"]["third"]["items"]
        assert "$ref" not in third_items
        assert "shared_field" in third_items["properties"]

    def test_inline_simple_refs_basemodel_reference(self):
        """Test _inline_simple_refs handles BaseModel references."""
        schema: Any = {"type": "object", "properties": {"base": {"$ref": "#/$defs/BaseModel"}}}

        SchemaGenerator._inline_simple_refs(schema, {})  # type: ignore[reportPrivateUsage]

        # BaseModel reference should be replaced with generic object
        base_prop = schema["properties"]["base"]
        assert "$ref" not in base_prop
        assert base_prop["type"] == "object"
        assert "Base model object" in base_prop["description"]

    def test_inline_simple_refs_openapi_style_references(self):
        """Test _inline_simple_refs handles OpenAPI-style references."""
        defs: Any = {"ComponentModel": {"type": "object", "properties": {"component_field": {"type": "boolean"}}}}

        schema: Any = {"type": "object", "properties": {"component": {"$ref": "#/components/schemas/ComponentModel"}}}

        SchemaGenerator._inline_simple_refs(schema, defs)  # type: ignore[reportPrivateUsage]

        # OpenAPI-style reference should be resolved
        component_prop = schema["properties"]["component"]
        assert "$ref" not in component_prop
        assert component_prop["type"] == "object"
        assert "component_field" in component_prop["properties"]

    def test_inline_simple_refs_preserves_other_schema_properties(self):
        """Test that _inline_simple_refs preserves non-reference schema properties."""
        defs: Any = {"RefModel": {"type": "object", "properties": {"ref_field": {"type": "string"}}}}

        schema: Any = {
            "type": "object",
            "title": "TestSchema",
            "description": "A test schema",
            "required": ["name", "referenced"],
            "properties": {
                "name": {"type": "string", "description": "Name field", "minLength": 1},
                "referenced": {"$ref": "#/$defs/RefModel"},
            },
            "additionalProperties": False,
        }

        SchemaGenerator._inline_simple_refs(schema, defs)  # type: ignore[reportPrivateUsage]

        # Non-reference properties should be preserved
        assert schema["type"] == "object"
        assert schema["title"] == "TestSchema"
        assert schema["description"] == "A test schema"
        assert schema["required"] == ["name", "referenced"]
        assert schema["additionalProperties"] is False

        # Non-reference property should be unchanged
        name_prop = schema["properties"]["name"]
        assert name_prop["type"] == "string"
        assert name_prop["description"] == "Name field"
        assert name_prop["minLength"] == 1

        # Reference should be inlined
        ref_prop = schema["properties"]["referenced"]
        assert "$ref" not in ref_prop
        assert ref_prop["type"] == "object"

    def test_generate_response_schema_with_pydantic_model(self):
        """Test response schema generation with Pydantic models."""

        # Create test function
        def test_func() -> SimpleModel:
            return SimpleModel(name="test", value=42)

        # Create a mock RouteInfo
        test_func_: Callable[..., Any] = test_func
        sig = inspect.signature(test_func)
        route_info = RouteInfo(
            method=HTTPMethod.GET,
            endpoint=test_func_,
            signature=sig,
            parameters=sig.parameters,
            path_params=[],
            type_hints={"return": SimpleModel},
            description="Test route",
        )

        component_schemas: dict[str, dict[str, Any]] = {}

        response_schema = SchemaGenerator._generate_response_schema(route_info, component_schemas)  # type: ignore[reportPrivateUsage]

        # Should create a reference to the component schema
        assert response_schema == {"$ref": "#/components/schemas/SimpleModel"}

        # Should add the model to component schemas
        assert "SimpleModel" in component_schemas
        assert component_schemas["SimpleModel"]["type"] == "object"

    def test_generate_openapi_schema_integration(self):
        """Test full OpenAPI schema generation with our improvements."""
        from cognite_typed_functions.routing import RouteInfo

        # Create test function
        def test_nested_func(nested: NestedModel) -> NestedModel:
            return nested

        test_nested_func_: Callable[..., Any] = test_nested_func

        # Create route with nested model
        sig = inspect.signature(test_nested_func)
        route_info = RouteInfo(
            method=HTTPMethod.POST,
            endpoint=test_nested_func_,
            signature=sig,
            parameters=sig.parameters,
            path_params=[],
            type_hints={"nested": NestedModel, "return": NestedModel},
            description="Test nested model route",
        )

        routes = {"/nested": {HTTPMethod.POST: route_info}}

        # Generate schema
        schema = SchemaGenerator.generate_openapi_schema(title="Test API", version="1.0.0", routes=routes)

        # Verify basic OpenAPI structure
        assert schema["openapi"] == "3.1.0"
        assert schema["info"]["title"] == "Test API"
        assert "components" in schema
        assert "schemas" in schema["components"]

        # Should have our nested model in components
        schemas = schema["components"]["schemas"]
        assert "NestedModel" in schemas

        # NestedModel should have properly inlined references
        nested_schema = schemas["NestedModel"]
        assert nested_schema["type"] == "object"
        assert "properties" in nested_schema

        # SimpleModel should be inlined into NestedModel's 'simple' property
        # (this verifies our _inline_simple_refs is working correctly)
        simple_property = nested_schema["properties"]["simple"]
        assert "$ref" not in simple_property  # Reference should be inlined
        assert simple_property["type"] == "object"
        assert "name" in simple_property["properties"]
        assert "value" in simple_property["properties"]


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_defs(self):
        """Test with empty definitions."""
        schema = {"$ref": "#/$defs/NonExistent"}
        SchemaGenerator._inline_simple_refs(schema, {})  # type: ignore[reportPrivateUsage]

        # Should leave non-existent reference unchanged
        assert schema["$ref"] == "#/$defs/NonExistent"

    def test_invalid_ref_format(self):
        """Test with invalid reference format."""
        schema = {"$ref": "invalid-ref-format"}
        defs = {"SomeModel": {"type": "object"}}

        SchemaGenerator._inline_simple_refs(schema, defs)  # type: ignore[reportPrivateUsage]

        # Should leave invalid reference unchanged
        assert schema["$ref"] == "invalid-ref-format"

    def test_none_values(self):
        """Test with None values in schema."""
        schema: Any = {"type": "object", "properties": {"nullable": None, "valid": {"type": "string"}}}

        # Should not raise error
        SchemaGenerator._inline_simple_refs(schema, {})  # type: ignore[reportPrivateUsage]

        assert schema["properties"]["nullable"] is None
        assert schema["properties"]["valid"]["type"] == "string"


class TestPythonTypeToOpenAPIMapping:
    """Test the _python_type_to_openapi method improvements."""

    def test_basic_type_mappings(self):
        """Test basic Python type to OpenAPI type mappings."""
        mappings = [
            (int, "integer"),
            (float, "number"),
            (bool, "boolean"),
            (str, "string"),
            (dict, "object"),  # This was broken before - mapped to "string"
            (list, "array"),  # This was broken before - mapped to "string"
        ]

        for python_type, expected_openapi_type in mappings:
            result = SchemaGenerator._python_type_to_openapi(python_type)  # type: ignore[reportPrivateUsage]
            assert result == expected_openapi_type, f"Expected {expected_openapi_type} for {python_type}, got {result}"

    def test_typed_generic_mappings(self):
        """Test typing generics map correctly."""
        # Typed generics should map to base types
        assert SchemaGenerator._python_type_to_openapi(dict[str, str]) == "object"  # type: ignore[reportPrivateUsage]
        assert SchemaGenerator._python_type_to_openapi(list[int]) == "array"  # type: ignore[reportPrivateUsage]
        assert SchemaGenerator._python_type_to_openapi(list[dict[str, str]]) == "array"  # type: ignore[reportPrivateUsage]

    def test_unknown_type_fallback(self):
        """Test unknown types fall back to string."""

        class CustomType:
            pass

        # Unknown types should fall back to "string"
        assert SchemaGenerator._python_type_to_openapi(CustomType) == "string"  # type: ignore[reportPrivateUsage]


class TestRequestBodySchemaGeneration:
    """Test request body schema generation for POST/PUT methods."""

    def test_single_pydantic_model_request_body(self):
        """Test request body with single Pydantic model."""

        def test_func(model: SimpleModel) -> SimpleModel:
            return model

        test_func_: Callable[..., Any] = test_func
        sig = inspect.signature(test_func)
        route_info = RouteInfo(
            method=HTTPMethod.POST,
            endpoint=test_func_,
            signature=sig,
            parameters=sig.parameters,
            path_params=[],
            type_hints={"model": SimpleModel, "return": SimpleModel},
            description="Test route",
        )

        routes = {"/test": {HTTPMethod.POST: route_info}}
        schema = SchemaGenerator.generate_openapi_schema("Test API", "1.0.0", routes)

        # Should have request body
        post_op = schema["paths"]["/test"]["post"]
        assert "requestBody" in post_op

        request_body = post_op["requestBody"]
        assert request_body["required"] is True
        assert "application/json" in request_body["content"]

        # Should reference the model in components
        request_schema = request_body["content"]["application/json"]["schema"]
        assert request_schema == {"$ref": "#/components/schemas/SimpleModel"}

        # Model should be in components
        assert "SimpleModel" in schema["components"]["schemas"]

    def test_multiple_pydantic_models_request_body(self):
        """Test request body with multiple Pydantic models."""

        def test_func(model1: SimpleModel, model2: NestedModel) -> SimpleModel:
            return model1

        test_func_: Callable[..., Any] = test_func
        sig = inspect.signature(test_func)
        route_info = RouteInfo(
            method=HTTPMethod.POST,
            endpoint=test_func_,
            signature=sig,
            parameters=sig.parameters,
            path_params=[],
            type_hints={"model1": SimpleModel, "model2": NestedModel, "return": SimpleModel},
            description="Test route",
        )

        routes = {"/test": {HTTPMethod.POST: route_info}}
        schema = SchemaGenerator.generate_openapi_schema("Test API", "1.0.0", routes)

        # Should have request body with object containing both models
        request_body = schema["paths"]["/test"]["post"]["requestBody"]
        request_schema = request_body["content"]["application/json"]["schema"]

        assert request_schema["type"] == "object"
        assert "properties" in request_schema
        assert "model1" in request_schema["properties"]
        assert "model2" in request_schema["properties"]
        assert request_schema["required"] == ["model1", "model2"]

        # Both models should reference components
        assert request_schema["properties"]["model1"] == {"$ref": "#/components/schemas/SimpleModel"}
        assert request_schema["properties"]["model2"] == {"$ref": "#/components/schemas/NestedModel"}

    def test_get_method_no_request_body(self):
        """Test GET methods don't get request body even with Pydantic models."""

        def test_func(model: SimpleModel) -> SimpleModel:
            return model

        test_func_: Callable[..., Any] = test_func
        sig = inspect.signature(test_func)
        route_info = RouteInfo(
            method=HTTPMethod.GET,
            endpoint=test_func_,
            signature=sig,
            parameters=sig.parameters,
            path_params=[],
            type_hints={"model": SimpleModel, "return": SimpleModel},
            description="Test route",
        )

        routes = {"/test": {HTTPMethod.GET: route_info}}
        schema = SchemaGenerator.generate_openapi_schema("Test API", "1.0.0", routes)

        # Should NOT have request body for GET
        get_op = schema["paths"]["/test"]["get"]
        assert "requestBody" not in get_op

        # Should have query parameter instead
        params = get_op["parameters"]
        # Note: Pydantic models in GET should be skipped from query params too
        # (they can't be serialized as query strings)
        assert len(params) == 0

    def test_mixed_parameters_request_body(self):
        """Test mixed parameters - some Pydantic models, some primitives."""

        def test_func(model: SimpleModel, name: str, count: int) -> SimpleModel:
            return model

        test_func_: Callable[..., Any] = test_func
        sig = inspect.signature(test_func)
        route_info = RouteInfo(
            method=HTTPMethod.POST,
            endpoint=test_func_,
            signature=sig,
            parameters=sig.parameters,
            path_params=[],
            type_hints={"model": SimpleModel, "name": str, "count": int, "return": SimpleModel},
            description="Test route",
        )

        routes = {"/test": {HTTPMethod.POST: route_info}}
        schema = SchemaGenerator.generate_openapi_schema("Test API", "1.0.0", routes)

        post_op = schema["paths"]["/test"]["post"]

        # Should have request body for Pydantic model
        assert "requestBody" in post_op
        request_schema = post_op["requestBody"]["content"]["application/json"]["schema"]
        assert request_schema == {"$ref": "#/components/schemas/SimpleModel"}

        # Should have query parameters for primitives
        params = post_op["parameters"]
        param_names = {p["name"] for p in params}
        assert "name" in param_names
        assert "count" in param_names
        assert len(params) == 2


class TestResponseSchemaGeneration:
    """Test response schema generation improvements."""

    def test_list_of_pydantic_models_response(self):
        """Test response schema for List[PydanticModel]."""

        def test_func() -> list[SimpleModel]:
            return []

        test_func_: Callable[..., Any] = test_func
        sig = inspect.signature(test_func)
        route_info = RouteInfo(
            method=HTTPMethod.GET,
            endpoint=test_func_,
            signature=sig,
            parameters=sig.parameters,
            path_params=[],
            type_hints={"return": list[SimpleModel]},
            description="Test route",
        )

        routes = {"/test": {HTTPMethod.GET: route_info}}
        schema = SchemaGenerator.generate_openapi_schema("Test API", "1.0.0", routes)

        # Response should be array of model references
        response_schema = schema["paths"]["/test"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
        assert response_schema["type"] == "array"
        assert response_schema["items"] == {"$ref": "#/components/schemas/SimpleModel"}

        # Model should be in components
        assert "SimpleModel" in schema["components"]["schemas"]

    def test_list_of_primitives_response(self):
        """Test response schema for List[primitive]."""

        def test_func() -> list[str]:
            return []

        test_func_: Callable[..., Any] = test_func
        sig = inspect.signature(test_func)
        route_info = RouteInfo(
            method=HTTPMethod.GET,
            endpoint=test_func_,
            signature=sig,
            parameters=sig.parameters,
            path_params=[],
            type_hints={"return": list[str]},
            description="Test route",
        )

        routes = {"/test": {HTTPMethod.GET: route_info}}
        schema = SchemaGenerator.generate_openapi_schema("Test API", "1.0.0", routes)

        # Response should be array of strings
        response_schema = schema["paths"]["/test"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
        assert response_schema["type"] == "array"
        assert response_schema["items"] == {"type": "string"}

    def test_dict_response(self):
        """Test response schema for dict return type."""

        def test_func() -> dict[str, str]:
            return {}

        test_func_: Callable[..., Any] = test_func
        sig = inspect.signature(test_func)
        route_info = RouteInfo(
            method=HTTPMethod.GET,
            endpoint=test_func_,
            signature=sig,
            parameters=sig.parameters,
            path_params=[],
            type_hints={"return": dict[str, str]},
            description="Test route",
        )

        routes = {"/test": {HTTPMethod.GET: route_info}}
        schema = SchemaGenerator.generate_openapi_schema("Test API", "1.0.0", routes)

        # Response should be object
        response_schema = schema["paths"]["/test"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
        assert response_schema == {"type": "object"}

    def test_no_return_type_fallback(self):
        """Test response schema when no return type is specified."""

        def test_func():
            return {"data": "test"}

        test_func_: Callable[..., Any] = test_func
        sig = inspect.signature(test_func)
        route_info = RouteInfo(
            method=HTTPMethod.GET,
            endpoint=test_func_,
            signature=sig,
            parameters=sig.parameters,
            path_params=[],
            type_hints={},  # No return type hint
            description="Test route",
        )

        routes = {"/test": {HTTPMethod.GET: route_info}}
        schema = SchemaGenerator.generate_openapi_schema("Test API", "1.0.0", routes)

        # Should fall back to generic object
        response_schema = schema["paths"]["/test"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
        assert response_schema == {"type": "object"}


class TestComponentSchemaManagement:
    """Test component schema deduplication and management."""

    def test_schema_deduplication(self):
        """Test that the same model is not duplicated in components."""

        def func1() -> SimpleModel:
            return SimpleModel(name="test", value=1)

        def func2(model: SimpleModel) -> SimpleModel:
            return model

        def func3() -> SimpleModel:
            return SimpleModel(name="test2", value=2)

        # Create multiple routes using the same model
        routes: dict[str, dict[HTTPMethod, RouteInfo]] = {}
        for i, func in enumerate([func1, func2, func3], 1):
            func_: Callable[..., Any] = func
            sig = inspect.signature(func)
            route_info = RouteInfo(
                method=HTTPMethod.POST if i == 2 else HTTPMethod.GET,
                endpoint=func_,
                signature=sig,
                parameters=sig.parameters,
                path_params=[],
                type_hints={"model": SimpleModel, "return": SimpleModel} if i == 2 else {"return": SimpleModel},
                description=f"Test route {i}",
            )
            routes[f"/test{i}"] = {HTTPMethod.POST if i == 2 else HTTPMethod.GET: route_info}

        schema = SchemaGenerator.generate_openapi_schema("Test API", "1.0.0", routes)

        # Should only have one instance of SimpleModel in components
        components = schema["components"]["schemas"]
        simple_model_count = sum(1 for name in components.keys() if name == "SimpleModel")
        assert simple_model_count == 1

        # All routes should reference the same component
        for i in range(1, 4):
            path_schema = schema["paths"][f"/test{i}"]
            method = "post" if i == 2 else "get"
            response_schema = path_schema[method]["responses"]["200"]["content"]["application/json"]["schema"]
            assert response_schema == {"$ref": "#/components/schemas/SimpleModel"}

    def test_parameter_type_mapping_in_openapi(self):
        """Integration test for parameter type mapping in full OpenAPI schema."""

        def test_func(
            int_param: int,
            str_param: str,
            dict_param: dict[str, str],
            list_param: list[str],
            typed_dict: dict[str, str],
            typed_list: list[int],
        ) -> dict[str, str]:
            return {}

        test_func_: Callable[..., Any] = test_func
        sig = inspect.signature(test_func)
        route_info = RouteInfo(
            method=HTTPMethod.GET,
            endpoint=test_func_,
            signature=sig,
            parameters=sig.parameters,
            path_params=[],
            type_hints={
                "int_param": int,
                "str_param": str,
                "dict_param": dict,
                "list_param": list,
                "typed_dict": dict[str, str],
                "typed_list": list[int],
                "return": dict,
            },
            description="Test parameter types",
        )

        routes = {"/test": {HTTPMethod.GET: route_info}}
        schema = SchemaGenerator.generate_openapi_schema("Test API", "1.0.0", routes)

        # Check parameter type mappings
        params = schema["paths"]["/test"]["get"]["parameters"]
        param_types = {p["name"]: p["schema"]["type"] for p in params}

        expected_types = {
            "int_param": "integer",
            "str_param": "string",
            "dict_param": "object",  # This was "string" before the fix
            "list_param": "array",  # This was "string" before the fix
            "typed_dict": "object",
            "typed_list": "array",
        }

        for param_name, expected_type in expected_types.items():
            assert param_types[param_name] == expected_type, (
                f"Parameter {param_name}: expected {expected_type}, got {param_types[param_name]}"
            )
