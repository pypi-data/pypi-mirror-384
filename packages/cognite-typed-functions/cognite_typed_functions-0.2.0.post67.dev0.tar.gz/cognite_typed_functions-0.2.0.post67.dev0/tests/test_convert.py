"""Tests for convert module."""

from collections.abc import Mapping
from typing import cast

import pytest
from cognite.client import CogniteClient
from pydantic import BaseModel

from .conftest import convert_with_di


class Item(BaseModel):
    """Test Pydantic model."""

    name: str
    value: int
    optional_field: str | None = None


class Category(BaseModel):
    """Another test Pydantic model."""

    category: str
    items: list[Item]


class User(BaseModel):
    """Test model for recursive type conversion."""

    name: str
    age: int


class Team(BaseModel):
    """Test model for deeply nested structures."""

    name: str
    leader: User
    members: list[User]


class TestConvertArgumentsToTypedParams:
    """Test suite for convert_arguments_to_typed_params function."""

    def test_basic_type_conversion(self, mock_client: CogniteClient):
        """Test basic type conversions (str to int, float, bool)."""

        def test_func(client: CogniteClient, count: int, rate: float, enabled: bool) -> dict[str, int | float | bool]:
            return {"count": count, "rate": rate, "enabled": enabled}

        arguments = {"count": "42", "rate": "3.14", "enabled": "true"}

        result = convert_with_di(mock_client, test_func, arguments)

        assert result["client"] == mock_client
        assert result["count"] == 42
        assert result["rate"] == 3.14
        assert result["enabled"] is True

    def test_boolean_conversion_variations(self, mock_client: CogniteClient):
        """Test different boolean string representations."""

        def test_func(client: CogniteClient, flag: bool) -> dict[str, bool]:
            return {"flag": flag}

        # Test various true values
        for true_val in ["true", "1", "yes", "on", "TRUE", "True"]:
            result = convert_with_di(mock_client, test_func, {"flag": true_val})
            assert result["flag"] is True, f"Failed for {true_val}"

        # Test false values
        for false_val in ["false", "0", "no", "off", "FALSE", "False", "anything"]:
            result = convert_with_di(mock_client, test_func, {"flag": false_val})
            assert result["flag"] is False, f"Failed for {false_val}"

    def test_pydantic_model_conversion(self, mock_client: CogniteClient):
        """Test conversion of dict to Pydantic model."""

        def test_func(client: CogniteClient, item: Item) -> dict[str, Item]:
            return {"item": item}

        arguments = {"item": {"name": "test item", "value": 100, "optional_field": "optional"}}

        result = convert_with_di(mock_client, test_func, arguments)

        assert result["client"] == mock_client
        assert isinstance(result["item"], Item)
        assert result["item"].name == "test item"
        assert result["item"].value == 100
        assert result["item"].optional_field == "optional"

    def test_pydantic_model_validation_error(self, mock_client: CogniteClient):
        """Test handling of Pydantic validation errors."""

        def test_func(client: CogniteClient, item: Item) -> dict[str, Item]:
            return {"item": item}

        # Missing required field 'value'
        arguments = {
            "item": {
                "name": "test item"
                # 'value' is missing and required
            }
        }

        with pytest.raises(ValueError, match="Validation error for parameter 'item'"):
            convert_with_di(mock_client, test_func, arguments)

    def test_list_of_pydantic_models_conversion(self, mock_client: CogniteClient):
        """Test conversion of list of dicts to list of Pydantic models."""

        def test_func(client: CogniteClient, items: list[Item]) -> dict[str, list[Item]]:
            return {"items": items}

        arguments = {
            "items": [
                {"name": "item1", "value": 10},
                {"name": "item2", "value": 20, "optional_field": "opt"},
            ]
        }

        result = convert_with_di(mock_client, test_func, arguments)

        assert result["client"] == mock_client
        assert isinstance(result["items"], list)
        result = cast(dict[str, object], result)
        result["items"] = cast(list[Item], result["items"])
        assert len(result["items"]) == 2

        assert isinstance(result["items"][0], Item)
        assert result["items"][0].name == "item1"
        assert result["items"][0].value == 10
        assert result["items"][0].optional_field is None

        assert isinstance(result["items"][1], Item)
        assert result["items"][1].name == "item2"
        assert result["items"][1].value == 20
        assert result["items"][1].optional_field == "opt"

    def test_list_of_pydantic_models_validation_error(self, mock_client: CogniteClient):
        """Test handling of validation errors in list of Pydantic models."""

        def test_func(client: CogniteClient, items: list[Item]) -> dict[str, list[Item]]:
            return {"items": items}

        arguments = {
            "items": [
                {"name": "item1", "value": 10},
                {"name": "item2"},  # Missing required 'value'
            ]
        }

        with pytest.raises(ValueError, match="Validation error for parameter 'items' \\(list\\)"):
            convert_with_di(mock_client, test_func, arguments)

    def test_mixed_parameter_types(self, mock_client: CogniteClient):
        """Test function with mix of different parameter types."""

        def test_func(
            client: CogniteClient,
            name: str,
            count: int,
            item: Item,
            items: list[Item],
            enabled: bool,
        ) -> dict[str, str | int | Item | list[Item] | bool]:
            return {
                "name": name,
                "count": count,
                "item": item,
                "items": items,
                "enabled": enabled,
            }

        arguments = {
            "name": "test function",
            "count": "42",
            "item": {"name": "single item", "value": 100},
            "items": [{"name": "list item", "value": 200}],
            "enabled": "true",
        }

        result = convert_with_di(mock_client, test_func, arguments)

        assert result["client"] == mock_client
        assert result["name"] == "test function"
        assert result["count"] == 42
        assert isinstance(result["item"], Item)
        assert result["item"].name == "single item"
        assert isinstance(result["items"], list)
        result = cast(dict[str, object], result)
        result["items"] = cast(list[Item], result["items"])
        assert len(result["items"]) == 1
        assert isinstance(result["items"][0], Item)
        assert result["enabled"] is True

    def test_parameters_not_in_signature(self, mock_client: CogniteClient):
        """Test handling of parameters not in function signature."""

        def test_func(client: CogniteClient, name: str) -> dict[str, str]:
            return {"name": name}

        arguments = {
            "name": "test",
            "extra_param": "should be included as-is",
            "another_extra": 42,
        }

        result = convert_with_di(mock_client, test_func, arguments)

        assert result["client"] == mock_client
        assert result["name"] == "test"
        assert result["extra_param"] == "should be included as-is"
        assert result["another_extra"] == 42

    def test_function_without_type_hints(self, mock_client: CogniteClient):
        """Test handling of functions without type hints.

        With AND semantics, framework dependencies require both name AND type.
        Parameters without type annotations are NOT treated as dependencies.
        """

        def test_func_no_hints(client, name, value):  # type: ignore No type hints
            return {"name": name, "value": value}  # type: ignore

        arguments = {"name": "test", "value": "123", "client": mock_client}

        result = convert_with_di(mock_client, test_func_no_hints, arguments)  # type: ignore[arg-type]

        # Without type hints, client is NOT a dependency and must come from arguments
        assert result["client"] == mock_client
        assert result["name"] == "test"
        assert result["value"] == "123"  # Stays as string since no type hints

    def test_type_conversion_validation_error(self, mock_client: CogniteClient):
        """Test that type conversion failures raise validation errors."""

        def test_func(client: CogniteClient, number: int) -> dict[str, int]:
            return {"number": number}

        arguments = {
            "number": "not-a-number"  # Should fail int() conversion
        }

        expected_msg = r"Validation error for parameter 'number': Cannot convert 'not-a-number' \(type str\) to int"
        with pytest.raises(ValueError, match=expected_msg):
            convert_with_di(mock_client, test_func, arguments)

    def test_non_string_values_preserved(self, mock_client: CogniteClient):
        """Test that non-string values are preserved as-is."""

        def test_func(client: CogniteClient, count: int, data: dict[str, str]) -> dict[str, int | dict[str, str]]:
            return {"count": count, "data": data}

        arguments = {
            "count": 42,  # Already an int
            "data": {"key": "value"},  # Already a dict
        }

        result = convert_with_di(mock_client, test_func, arguments)

        assert result["client"] == mock_client
        assert result["count"] == 42
        assert result["data"] == {"key": "value"}

    def test_client_parameter_handling(self, mock_client: CogniteClient):
        """Test that client parameter is always included."""

        def test_func(client: CogniteClient, name: str) -> dict[str, str]:
            return {"name": name}

        # Client in arguments will be processed but we also inject our client
        arguments = {"name": "test"}

        result = convert_with_di(mock_client, test_func, arguments)

        assert result["client"] == mock_client  # Should be our mock client
        assert result["name"] == "test"

    def test_client_parameter_invalid_override(self, mock_client: CogniteClient):
        """Test behavior when client is provided in arguments - should be ignored."""

        def test_func(client: CogniteClient, name: str) -> dict[str, str]:
            return {"name": name}

        # Provide a string in arguments for client - should be ignored by DI
        arguments = {"client": "invalid_client_string", "name": "test"}

        # Client from arguments should be ignored, injected client should be used
        result = convert_with_di(mock_client, test_func, arguments)
        assert result["client"] == mock_client  # Should be the injected mock, not the string
        assert result["name"] == "test"

    def test_empty_arguments(self, mock_client: CogniteClient):
        """Test handling of empty arguments."""

        def test_func(client: CogniteClient) -> dict[str, str]:
            return {"status": "ok"}

        result = convert_with_di(mock_client, test_func, {})

        assert result["client"] == mock_client
        assert len(result) == 1  # Only client parameter

    def test_unsupported_type_conversion(self, mock_client: CogniteClient):
        """Test strict validation for unsupported type conversions."""

        def test_func(client: CogniteClient, custom_obj: complex) -> dict[str, complex]:  # complex is not supported
            return {"obj": custom_obj}

        arguments = {"custom_obj": "some-string"}

        # Should raise validation error for unsupported type conversion
        expected_msg = r"Cannot convert 'some-string' \(type str\) to complex"
        with pytest.raises(ValueError, match=expected_msg):
            convert_with_di(mock_client, test_func, arguments)  # type: ignore[arg-type]

    def test_default_parameters(self, mock_client: CogniteClient):
        """Test handling of function default parameters."""

        def test_func(
            client: CogniteClient,
            name: str,
            count: int = 10,
            enabled: bool = True,
            optional_text: str | None = None,
        ) -> dict[str, str | int | bool | str | None]:
            return {
                "name": name,
                "count": count,
                "enabled": enabled,
                "optional_text": optional_text,
            }

        # Only provide required parameter
        arguments = {"name": "test"}

        result = convert_with_di(mock_client, test_func, arguments)

        # Should include default values
        assert result["client"] == mock_client
        assert result["name"] == "test"
        assert result["count"] == 10  # default value
        assert result["enabled"] is True  # default value
        assert result["optional_text"] is None  # default value

    def test_default_parameters_with_overrides(self, mock_client: CogniteClient):
        """Test that provided values override defaults."""

        def test_func(
            client: CogniteClient, name: str, count: int = 10, enabled: bool = True
        ) -> dict[str, str | int | bool]:
            return {"name": name, "count": count, "enabled": enabled}

        # Provide some defaults explicitly
        arguments = {"name": "test", "count": "42"}  # Override default count

        result = convert_with_di(mock_client, test_func, arguments)

        # Should use provided value and defaults for others
        assert result["client"] == mock_client
        assert result["name"] == "test"
        assert result["count"] == 42  # Overridden and converted from string
        assert result["enabled"] is True  # Still uses default

    def test_default_parameters_complex_types(self, mock_client: CogniteClient):
        """Test default parameters with complex types like Pydantic models."""

        def test_func(
            client: CogniteClient,
            name: str,
            default_item: Item = Item(name="default", value=0),
        ) -> dict[str, str | Item]:
            return {"name": name, "default_item": default_item}

        # Only provide required parameter
        arguments = {"name": "test"}

        result = convert_with_di(mock_client, test_func, arguments)

        # Should include default Pydantic model
        assert result["client"] == mock_client
        assert result["name"] == "test"
        assert isinstance(result["default_item"], Item)
        assert result["default_item"].name == "default"
        assert result["default_item"].value == 0

    # === NEW RECURSIVE TYPE CONVERSION TESTS ===

    def test_dict_with_basemodel_values(self, mock_client: CogniteClient):
        """Test recursive conversion of dict[str, BaseModel]."""

        def test_func(client: CogniteClient, users: dict[str, User]) -> dict[str, dict[str, User]]:
            return {"users": users}

        arguments = {
            "users": {
                "admin": {"name": "Alice", "age": 30},
                "user": {"name": "Bob", "age": 25},
            }
        }

        result = convert_with_di(mock_client, test_func, arguments)

        assert result["client"] == mock_client
        assert isinstance(result["users"], dict)
        assert "admin" in result["users"]
        assert "user" in result["users"]
        assert isinstance(result["users"]["admin"], User)
        assert isinstance(result["users"]["user"], User)
        assert result["users"]["admin"].name == "Alice"
        assert result["users"]["admin"].age == 30
        assert result["users"]["user"].name == "Bob"
        assert result["users"]["user"].age == 25

    def test_optional_basemodel_with_value(self, mock_client: CogniteClient):
        """Test Optional[BaseModel] conversion with a value."""

        def test_func(client: CogniteClient, user: User | None) -> dict[str, User | None]:
            return {"user": user}

        arguments = {"user": {"name": "Charlie", "age": 35}}

        result = convert_with_di(mock_client, test_func, arguments)

        assert result["client"] == mock_client
        assert isinstance(result["user"], User)
        assert result["user"].name == "Charlie"
        assert result["user"].age == 35

    def test_optional_basemodel_with_none(self, mock_client: CogniteClient):
        """Test Optional[BaseModel] conversion with None."""

        def test_func(client: CogniteClient, user: User | None) -> dict[str, User | None]:
            return {"user": user}

        arguments = {"user": None}

        result = convert_with_di(mock_client, test_func, arguments)

        assert result["client"] == mock_client
        assert result["user"] is None

    def test_optional_basemodel_new_syntax(self, mock_client: CogniteClient):
        """Test Optional conversion with modern T | None syntax (Python 3.10+)."""

        def test_func(client: CogniteClient, user: User | None) -> dict[str, User | None]:
            return {"user": user}

        # Test with BaseModel
        arguments = {"user": {"name": "Charlie", "age": 35}}
        result = convert_with_di(mock_client, test_func, arguments)

        assert result["client"] == mock_client
        assert isinstance(result["user"], User)
        assert result["user"].name == "Charlie"
        assert result["user"].age == 35

        # Test with None
        arguments = {"user": None}
        result = convert_with_di(mock_client, test_func, arguments)

        assert result["client"] == mock_client
        assert result["user"] is None

    def test_union_type_conversion(self, mock_client: CogniteClient):
        """Test Union type conversion."""

        def test_func(client: CogniteClient, data: User | str) -> dict[str, User | str]:
            return {"data": data}

        # Test with BaseModel
        arguments = {"data": {"name": "Diana", "age": 40}}
        result = convert_with_di(mock_client, test_func, arguments)

        assert result["client"] == mock_client
        assert isinstance(result["data"], User)
        assert result["data"].name == "Diana"
        assert result["data"].age == 40

        # Test with string
        arguments = {"data": "just a string"}
        result = convert_with_di(mock_client, test_func, arguments)

        assert result["client"] == mock_client
        assert isinstance(result["data"], str)
        assert result["data"] == "just a string"

    def test_union_type_conversion_new_syntax(self, mock_client: CogniteClient):
        """Test Union type conversion with modern | syntax (Python 3.10+)."""

        def test_func(client: CogniteClient, data: User | str) -> dict[str, User | str]:
            return {"data": data}

        # Test with BaseModel
        arguments = {"data": {"name": "Diana", "age": 40}}
        result = convert_with_di(mock_client, test_func, arguments)

        assert result["client"] == mock_client
        assert isinstance(result["data"], User)
        assert result["data"].name == "Diana"
        assert result["data"].age == 40

        # Test with string
        arguments = {"data": "just a string"}
        result = convert_with_di(mock_client, test_func, arguments)

        assert result["client"] == mock_client
        assert isinstance(result["data"], str)
        assert result["data"] == "just a string"

    def test_deeply_nested_basemodel(self, mock_client: CogniteClient):
        """Test deeply nested BaseModel with list[BaseModel]."""

        def test_func(client: CogniteClient, team: Team) -> dict[str, Team]:
            return {"team": team}

        arguments = {
            "team": {
                "name": "Engineering",
                "leader": {"name": "Eve", "age": 45},
                "members": [{"name": "Frank", "age": 28}, {"name": "Grace", "age": 32}],
            }
        }

        result = convert_with_di(mock_client, test_func, arguments)

        assert result["client"] == mock_client
        assert isinstance(result["team"], Team)
        assert result["team"].name == "Engineering"
        assert isinstance(result["team"].leader, User)
        assert result["team"].leader.name == "Eve"
        assert result["team"].leader.age == 45
        assert isinstance(result["team"].members, list)
        assert len(result["team"].members) == 2
        assert isinstance(result["team"].members[0], User)
        assert isinstance(result["team"].members[1], User)
        assert result["team"].members[0].name == "Frank"
        assert result["team"].members[0].age == 28
        assert result["team"].members[1].name == "Grace"
        assert result["team"].members[1].age == 32

    def test_list_of_dict_with_basemodel(self, mock_client: CogniteClient):
        """Test super nested: list[dict[str, BaseModel]]."""

        def test_func(client: CogniteClient, data: list[dict[str, User]]) -> dict[str, list[dict[str, User]]]:
            return {"data": data}

        arguments = {
            "data": [
                {"lead": {"name": "Henry", "age": 50}},
                {"dev": {"name": "Iris", "age": 29}, "qa": {"name": "Jack", "age": 31}},
            ]
        }

        result = convert_with_di(mock_client, test_func, arguments)

        assert result["client"] == mock_client
        assert isinstance(result["data"], list)
        result = cast(dict[str, object], result)
        result["data"] = cast(list[dict[str, User]], result["data"])
        assert len(result["data"]) == 2

        # First dict
        assert isinstance(result["data"][0], dict)
        assert "lead" in result["data"][0]
        assert isinstance(result["data"][0]["lead"], User)
        assert result["data"][0]["lead"].name == "Henry"
        assert result["data"][0]["lead"].age == 50

        # Second dict
        assert isinstance(result["data"][1], dict)
        assert "dev" in result["data"][1]
        assert "qa" in result["data"][1]
        assert isinstance(result["data"][1]["dev"], User)
        assert isinstance(result["data"][1]["qa"], User)
        assert result["data"][1]["dev"].name == "Iris"
        assert result["data"][1]["dev"].age == 29
        assert result["data"][1]["qa"].name == "Jack"
        assert result["data"][1]["qa"].age == 31

    def test_dict_with_list_of_basemodel(self, mock_client: CogniteClient):
        """Test dict[str, list[BaseModel]] conversion."""

        def test_func(client: CogniteClient, teams: dict[str, list[User]]) -> dict[str, dict[str, list[User]]]:
            return {"teams": teams}

        arguments = {
            "teams": {
                "frontend": [{"name": "Kate", "age": 27}, {"name": "Leo", "age": 33}],
                "backend": [{"name": "Maya", "age": 29}],
            }
        }

        result: Mapping[str, object] = convert_with_di(mock_client, test_func, arguments)

        assert result["client"] == mock_client
        assert isinstance(result["teams"], dict)
        assert "frontend" in result["teams"]
        assert "backend" in result["teams"]

        # Frontend team
        assert isinstance(result["teams"]["frontend"], list)
        result["teams"]["frontend"] = cast(list[User], result["teams"]["frontend"])
        assert len(result["teams"]["frontend"]) == 2
        assert isinstance(result["teams"]["frontend"][0], User)
        assert isinstance(result["teams"]["frontend"][1], User)
        assert result["teams"]["frontend"][0].name == "Kate"
        assert result["teams"]["frontend"][0].age == 27
        assert result["teams"]["frontend"][1].name == "Leo"
        assert result["teams"]["frontend"][1].age == 33

        # Backend team
        assert isinstance(result["teams"]["backend"], list)
        result["teams"]["backend"] = cast(list[User], result["teams"]["backend"])
        assert len(result["teams"]["backend"]) == 1
        assert isinstance(result["teams"]["backend"][0], User)
        assert result["teams"]["backend"][0].name == "Maya"
        assert result["teams"]["backend"][0].age == 29

    def test_recursive_error_handling_with_path(self, mock_client: CogniteClient):
        """Test error handling preserves path information in recursive conversions."""

        def test_func(client: CogniteClient, data: dict[str, list[User]]) -> dict[str, dict[str, list[User]]]:
            return {"data": data}

        # Missing required field in nested structure
        arguments = {
            "data": {
                "team": [
                    {"name": "Valid", "age": 25},
                    {"name": "Invalid"},  # Missing 'age' field
                ]
            }
        }

        with pytest.raises(ValueError, match=r"Validation error for User at data\[team\]\[1\]"):
            convert_with_di(mock_client, test_func, arguments)

    def test_optional_with_union_fallback(self, mock_client: CogniteClient):
        """Test Optional[Union[...]] complex type."""

        def test_func(client: CogniteClient, data: User | str | None) -> dict[str, User | str | None]:
            return {"data": data}

        # Test with None
        arguments = {"data": None}
        result = convert_with_di(mock_client, test_func, arguments)
        assert result["data"] is None

        # Test with User
        arguments = {"data": {"name": "Nina", "age": 26}}
        result = convert_with_di(mock_client, test_func, arguments)
        assert isinstance(result["data"], User)
        assert result["data"].name == "Nina"

        # Test with string
        arguments = {"data": "text value"}
        result = convert_with_di(mock_client, test_func, arguments)
        assert result["data"] == "text value"
