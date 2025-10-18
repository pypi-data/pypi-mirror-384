"""Property-based tests for convert module using Hypothesis.

This module uses property-based testing to thoroughly test the type conversion
system with automatically generated test cases.
"""

import re
from types import UnionType
from typing import Any, Optional, Union, cast

import pytest
from cognite.client import CogniteClient
from hypothesis import assume, given
from hypothesis import strategies as st
from hypothesis.strategies import DrawFn
from pydantic import BaseModel

from cognite_typed_functions.models import TypedResponse

from .conftest import convert_with_di


# Test Models
class Item(BaseModel):
    """Test Pydantic model."""

    name: str
    value: int
    optional_field: str | None = None


class User(BaseModel):
    """Test model for recursive type conversion."""

    name: str
    age: int


class Team(BaseModel):
    """Test model for deeply nested structures."""

    name: str
    leader: User
    members: list[User]


# Custom strategies
@st.composite
def valid_int_strings(draw: DrawFn) -> str:
    """Generate strings that should convert to integers."""
    value = draw(st.integers())
    return str(value)


@st.composite
def valid_float_strings(draw: DrawFn) -> str:
    """Generate strings that should convert to floats."""
    value = draw(st.floats(allow_nan=False, allow_infinity=False))
    return str(value)


@st.composite
def valid_bool_strings(draw: DrawFn) -> tuple[str, bool]:
    """Generate strings that should convert to booleans."""
    true_values = ["true", "1", "yes", "on", "TRUE", "True"]
    false_values = ["false", "0", "no", "off", "FALSE", "False", "anything_else"]

    is_truthy = draw(st.booleans())
    if is_truthy:
        return draw(st.sampled_from(true_values)), True
    else:
        return draw(st.sampled_from(false_values)), False


@st.composite
def item_dict(draw: DrawFn) -> dict[str, Any]:
    """Generate valid Item model dictionaries."""
    name = draw(st.text(min_size=1, max_size=50))
    value = draw(st.integers())
    optional_field = draw(st.one_of(st.none(), st.text(max_size=50)))

    item_data = {"name": name, "value": value}
    if optional_field is not None:
        item_data["optional_field"] = optional_field

    return item_data


@st.composite
def user_dict(draw: DrawFn) -> dict[str, Any]:
    """Generate valid User model dictionaries."""
    name = draw(st.text(min_size=1, max_size=50))
    age = draw(st.integers(min_value=0, max_value=150))
    return {"name": name, "age": age}


@st.composite
def team_dict(draw: DrawFn) -> dict[str, Any]:
    """Generate valid Team model dictionaries."""
    name = draw(st.text(min_size=1, max_size=50))
    leader = draw(user_dict())
    members = draw(st.lists(user_dict(), min_size=0, max_size=5))

    return {"name": name, "leader": leader, "members": members}


@st.composite
def union_type_data(draw: DrawFn) -> tuple[str, UnionType, Any]:
    """Generate union type configurations with appropriate test data."""
    union_configs = [
        (
            "Union[User, str]",
            Union[User, str],  #  # noqa: UP007
            st.one_of(user_dict(), st.text(min_size=1, max_size=50)),
        ),
        ("User | None", User | None, st.one_of(user_dict(), st.none())),
        ("Optional[User]", Optional[User], st.one_of(user_dict(), st.none())),  # noqa: UP045
        (
            "Union[User, str, None]",
            Union[User, str, None],  # noqa: UP007
            st.one_of(user_dict(), st.text(min_size=1, max_size=50), st.none()),
        ),
    ]

    config_name, union_type, data_strategy = draw(st.sampled_from(union_configs))
    test_data = draw(data_strategy)

    return config_name, union_type, test_data


class TestPropertyBasedConversion:
    """Property-based tests for type conversion."""

    @given(valid_int_strings())
    def test_string_to_int_conversion_property(self, mock_client: CogniteClient, int_string: str) -> None:
        """Property test: valid integer strings should convert to integers."""

        def test_func(client: CogniteClient, number: int) -> dict[str, int]:
            return {"number": number}

        arguments = {"number": int_string}
        result = convert_with_di(mock_client, test_func, arguments)

        assert isinstance(result["number"], int)
        assert result["number"] == int(int_string)

    @given(st.one_of(valid_float_strings(), valid_int_strings()))
    def test_string_to_float_conversion_property(self, mock_client: CogniteClient, float_string: str) -> None:
        """Property test: valid float strings and integer strings should convert to floats."""

        def test_func(client: CogniteClient, number: float) -> dict[str, float]:
            return {"number": number}

        arguments = {"number": float_string}
        result = convert_with_di(mock_client, test_func, arguments)

        assert isinstance(result["number"], float)
        assert result["number"] == float(float_string)

    @given(valid_bool_strings())
    def test_string_to_bool_conversion_property(self, mock_client: CogniteClient, bool_data: tuple[str, bool]) -> None:
        """Property test: boolean strings should convert according to truthy rules."""
        bool_string, expected = bool_data

        def test_func(client: CogniteClient, flag: bool) -> dict[str, bool]:
            return {"flag": flag}

        arguments = {"flag": bool_string}
        result = convert_with_di(mock_client, test_func, arguments)

        assert isinstance(result["flag"], bool)
        assert result["flag"] == expected

    @given(st.text())
    def test_invalid_int_conversion_raises_error(self, mock_client: CogniteClient, text: str) -> None:
        """Property test: invalid integer strings should raise validation errors."""
        assume(not text.lstrip("-").isdigit())  # Assume it's not a valid int
        assume(text)  # Assume non-empty string to avoid empty string edge case

        def test_func(client: CogniteClient, number: int) -> dict[str, int]:
            return {"number": number}

        arguments = {"number": text}

        # Should raise validation error for invalid conversion
        with pytest.raises(
            ValueError,
            match=rf"Validation error for parameter 'number': Cannot convert '{re.escape(text)}' \(type str\) to int",
        ):
            convert_with_di(mock_client, test_func, arguments)

    @given(item_dict())
    def test_basemodel_conversion_property(self, mock_client: CogniteClient, item_data: dict[str, Any]) -> None:
        """Property test: valid dictionaries should convert to BaseModel instances."""

        def test_func(client: CogniteClient, item: Item) -> TypedResponse:
            return {"item": item}

        arguments = {"item": item_data}
        result = convert_with_di(mock_client, test_func, arguments)

        assert isinstance(result["item"], Item)
        assert result["item"].name == item_data["name"]
        assert result["item"].value == item_data["value"]
        if "optional_field" in item_data:
            assert result["item"].optional_field == item_data["optional_field"]

    @given(st.lists(item_dict(), min_size=0, max_size=10))
    def test_list_basemodel_conversion_property(
        self, mock_client: CogniteClient, item_list: list[dict[str, Any]]
    ) -> None:
        """Property test: lists of valid dictionaries should convert to lists of BaseModels."""

        def test_func(client: CogniteClient, items: list[Item]) -> TypedResponse:
            return {"items": items}

        arguments: dict[str, Any] = {"items": item_list}
        result = convert_with_di(mock_client, test_func, arguments)

        assert isinstance(result["items"], list)
        result = cast(dict[str, object], result)
        result["items"] = cast(list[Item], result["items"])
        assert len(result["items"]) == len(item_list)
        for i, item in enumerate(result["items"]):
            assert isinstance(item, Item)
            assert item.name == item_list[i]["name"]
            assert item.value == item_list[i]["value"]

    @given(st.dictionaries(st.text(min_size=1, max_size=20), user_dict(), min_size=0, max_size=5))
    def test_dict_basemodel_conversion_property(
        self, mock_client: CogniteClient, user_dict_data: dict[str, dict[str, Any]]
    ) -> None:
        """Property test: dictionaries with BaseModel values should convert properly."""

        def test_func(client: CogniteClient, users: dict[str, User]) -> dict[str, dict[str, User]]:
            return {"users": users}

        arguments: dict[str, Any] = {"users": user_dict_data}
        result = convert_with_di(mock_client, test_func, arguments)

        assert isinstance(result["users"], dict)
        result = cast(dict[str, object], result)
        result["users"] = cast(dict[str, User], result["users"])
        assert len(result["users"]) == len(user_dict_data)
        for key, user in result["users"].items():
            assert isinstance(user, User)
            assert user.name == user_dict_data[key]["name"]
            assert user.age == user_dict_data[key]["age"]

    @given(st.one_of(st.none(), user_dict()))
    def test_optional_basemodel_property(self, mock_client: CogniteClient, user_data: dict[str, Any] | None) -> None:
        """Property test: Optional[BaseModel] should handle None and valid data."""

        def test_func(client: CogniteClient, user: User | None) -> TypedResponse:
            return {"user": user}

        arguments = {"user": user_data}
        result = convert_with_di(mock_client, test_func, arguments)

        if user_data is None:
            assert result["user"] is None
        else:
            assert isinstance(result["user"], User)
            assert result["user"].name == user_data["name"]
            assert result["user"].age == user_data["age"]

    @given(union_type_data())
    def test_union_type_conversion_property(
        self, mock_client: CogniteClient, union_data: tuple[str, UnionType, Any]
    ) -> None:
        """Property test: Union types should convert to the first matching type."""
        union_type_name, _union_type, data = union_data

        # Create the test function dynamically with the correct type annotation
        if union_type_name == "Union[User, str]":

            def test_func(client: CogniteClient, data: User | str) -> dict[str, User | str]:  # type: ignore[func-redefined]
                return {"data": data}
        elif union_type_name == "User | None":

            def test_func(client: CogniteClient, data: User | None) -> dict[str, User | None]:  # type: ignore[func-redefined]
                return {"data": data}
        elif union_type_name == "Optional[User]":

            def test_func(client: CogniteClient, data: User | None) -> dict[str, User | None]:  # type: ignore[func-redefined]
                return {"data": data}
        elif union_type_name == "Union[User, str, None]":

            def test_func(client: CogniteClient, data: User | str | None) -> dict[str, User | str | None]:  # type: ignore[func-redefined]
                return {"data": data}
        else:
            raise ValueError(f"Unknown union type: {union_type_name}")

        arguments = {"data": data}
        result = convert_with_di(mock_client, test_func, arguments)

        if data is None:
            # Should remain as None for Optional types and 3-way union
            assert result["data"] is None
        elif isinstance(data, dict):
            # Should convert to User
            assert isinstance(result["data"], User)
            assert result["data"].name == data["name"]
            assert result["data"].age == data["age"]
        else:
            # Should remain as string
            assert isinstance(result["data"], str)
            assert result["data"] == data

    @given(team_dict())
    def test_nested_basemodel_conversion_property(self, mock_client: CogniteClient, team_data: dict[str, Any]) -> None:
        """Property test: deeply nested BaseModels should convert recursively."""

        def test_func(client: CogniteClient, team: Team) -> dict[str, Team]:
            return {"team": team}

        arguments = {"team": team_data}
        result = convert_with_di(mock_client, test_func, arguments)

        assert isinstance(result["team"], Team)
        assert result["team"].name == team_data["name"]

        # Check leader conversion
        assert isinstance(result["team"].leader, User)
        assert result["team"].leader.name == team_data["leader"]["name"]
        assert result["team"].leader.age == team_data["leader"]["age"]

        # Check members conversion
        assert isinstance(result["team"].members, list)
        assert len(result["team"].members) == len(team_data["members"])
        for i, member in enumerate(result["team"].members):
            assert isinstance(member, User)
            assert member.name == team_data["members"][i]["name"]
            assert member.age == team_data["members"][i]["age"]

    @given(
        st.lists(
            st.dictionaries(st.text(min_size=1, max_size=10), user_dict(), min_size=1, max_size=3),
            min_size=0,
            max_size=3,
        )
    )
    def test_super_nested_conversion_property(
        self,
        mock_client: CogniteClient,
        nested_data: list[dict[str, dict[str, Any]]],
    ) -> None:
        """Property test: list[dict[str, BaseModel]] should convert properly."""

        def test_func(client: CogniteClient, data: list[dict[str, User]]) -> dict[str, list[dict[str, User]]]:
            return {"data": data}

        arguments: dict[str, Any] = {"data": nested_data}
        result = convert_with_di(mock_client, test_func, arguments)

        assert isinstance(result["data"], list)
        result = cast(dict[str, object], result)
        result["data"] = cast(list[dict[str, User]], result["data"])
        assert len(result["data"]) == len(nested_data)

        for i, dict_item in enumerate(result["data"]):
            assert isinstance(dict_item, dict)
            assert len(dict_item) == len(nested_data[i])

            for key, user in dict_item.items():
                assert isinstance(user, User)
                assert user.name == nested_data[i][key]["name"]
                assert user.age == nested_data[i][key]["age"]

    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=20),
            st.lists(user_dict(), min_size=0, max_size=5),
            min_size=0,
            max_size=3,
        )
    )
    def test_dict_with_list_conversion_property(
        self,
        mock_client: CogniteClient,
        teams_data: dict[str, list[dict[str, Any]]],
    ) -> None:
        """Property test: dict[str, list[BaseModel]] should convert properly."""

        def test_func(client: CogniteClient, teams: dict[str, list[User]]) -> dict[str, dict[str, list[User]]]:
            return {"teams": teams}

        arguments: dict[str, Any] = {"teams": teams_data}
        result = convert_with_di(mock_client, test_func, arguments)

        assert isinstance(result["teams"], dict)
        result = cast(dict[str, object], result)
        result["teams"] = cast(dict[str, list[User]], result["teams"])
        assert len(result["teams"]) == len(teams_data)

        for team_name, users in result["teams"].items():
            assert isinstance(users, list)
            assert len(users) == len(teams_data[team_name])

            for i, user in enumerate(users):
                assert isinstance(user, User)
                assert user.name == teams_data[team_name][i]["name"]
                assert user.age == teams_data[team_name][i]["age"]

    # Test invariants
    @given(st.integers(), st.floats(allow_nan=False, allow_infinity=False), st.booleans())
    def test_non_string_values_invariant(
        self,
        mock_client: CogniteClient,
        int_val: int,
        float_val: float,
        bool_val: bool,
    ) -> None:
        """Property test invariant: non-string values should be preserved as-is."""

        def test_func(client: CogniteClient, i: int, f: float, b: bool) -> dict[str, int | float | bool]:
            return {"i": i, "f": f, "b": b}

        arguments = {"i": int_val, "f": float_val, "b": bool_val}
        result = convert_with_di(mock_client, test_func, arguments)

        assert result["i"] == int_val
        assert result["f"] == float_val
        assert result["b"] == bool_val

    @given(st.dictionaries(st.text(min_size=1), st.text(), min_size=1, max_size=5))
    def test_extra_parameters_invariant(self, mock_client: CogniteClient, extra_params: dict[str, str]) -> None:
        """Property test invariant: parameters not in signature should be preserved."""

        def test_func(client: CogniteClient, name: str) -> dict[str, str]:
            return {"name": name}

        arguments = {"name": "test", **extra_params}
        result = convert_with_di(mock_client, test_func, arguments)

        assert result["name"] == "test"
        for key, value in extra_params.items():
            assert result[key] == value


# Error handling property tests
class TestPropertyBasedErrorHandling:
    """Property-based tests for error handling."""

    @given(st.dictionaries(st.text(min_size=1), st.text(), min_size=1, max_size=5))
    def test_invalid_basemodel_data_property(self, mock_client: CogniteClient, invalid_data: dict[str, str]) -> None:
        """Property test: invalid BaseModel data should raise validation errors."""
        assume("name" not in invalid_data or "value" not in invalid_data)  # Ensure it's invalid

        def test_func(client: CogniteClient, item: Item) -> dict[str, Item]:
            return {"item": item}

        arguments: dict[str, Any] = {"item": invalid_data}

        with pytest.raises(ValueError, match="Validation error"):
            convert_with_di(mock_client, test_func, arguments)

    @given(
        st.lists(
            st.dictionaries(st.text(), st.text(), min_size=1, max_size=5),
            min_size=1,
            max_size=3,
        )
    )
    def test_invalid_list_basemodel_property(
        self, mock_client: CogniteClient, invalid_list: list[dict[str, str]]
    ) -> None:
        """Property test: lists with invalid BaseModel data should raise errors."""
        # Ensure at least one item is invalid
        assume(not all("name" in item and "value" in item for item in invalid_list))

        def test_func(client: CogniteClient, items: list[Item]) -> dict[str, list[Item]]:
            return {"items": items}

        arguments: dict[str, Any] = {"items": invalid_list}

        with pytest.raises(ValueError, match="Validation error"):
            convert_with_di(mock_client, test_func, arguments)
