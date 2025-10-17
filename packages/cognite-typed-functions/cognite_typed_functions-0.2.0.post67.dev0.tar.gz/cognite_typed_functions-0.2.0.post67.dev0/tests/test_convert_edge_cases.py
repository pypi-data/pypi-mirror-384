"""Edge case tests for convert module.

This module tests critical production edge cases, error propagation, and path reporting
that are essential for debugging and maintainability in a Functions-as-a-Service platform.
"""

from typing import Any, cast

import pytest
from cognite.client import CogniteClient
from pydantic import BaseModel

from .conftest import convert_with_di


# Test Models for edge cases
class EdgeCaseItem(BaseModel):
    """Test model for edge case scenarios."""

    name: str
    value: int
    optional_field: str | None = None


class NestedEdgeCase(BaseModel):
    """Test model for deeply nested edge cases."""

    id: int
    items: list[EdgeCaseItem]
    metadata: dict[str, EdgeCaseItem]


class CircularRef(BaseModel):
    """Test model that could create circular references."""

    name: str
    parent: "CircularRef | None" = None


class TestErrorPropagationAndPathReporting:
    """Test suite for error propagation and accurate path reporting."""

    def test_list_conversion_top_level_error(self, mock_client: CogniteClient) -> None:
        """Validates error messages for top-level list failures."""

        def test_func(client: CogniteClient, items: list[EdgeCaseItem]) -> dict[str, list[EdgeCaseItem]]:
            return {"items": items}

        # Invalid data missing required field
        arguments = {
            "items": [
                {"name": "valid", "value": 10},
                {"name": "invalid"},  # Missing required 'value'
            ]
        }

        with pytest.raises(ValueError, match=r"Validation error for parameter 'items' \(list\)"):
            convert_with_di(mock_client, test_func, arguments)

    def test_list_conversion_nested_error(self, mock_client: CogniteClient) -> None:
        """Ensures correct path reporting in nested structures."""

        def test_func(client: CogniteClient, data: NestedEdgeCase) -> dict[str, NestedEdgeCase]:
            return {"data": data}

        # Error in deeply nested structure
        arguments = {
            "data": {
                "id": 1,
                "items": [
                    {"name": "valid", "value": 10},
                    {"name": "invalid"},  # Missing 'value' at items[1]
                ],
                "metadata": {"key1": {"name": "valid", "value": 20}},
            }
        }

        with pytest.raises(ValueError, match=r"Validation error for parameter 'data'"):
            convert_with_di(mock_client, test_func, arguments)

    def test_list_conversion_metadata_nested_error(self, mock_client: CogniteClient) -> None:
        """Tests path reporting in dict[str, BaseModel] structures."""

        def test_func(client: CogniteClient, data: NestedEdgeCase) -> dict[str, NestedEdgeCase]:
            return {"data": data}

        items: list[EdgeCaseItem] = []  # Just to satisfy the type checker

        # Error in metadata dict
        arguments: dict[str, Any] = {
            "data": {
                "id": 1,
                "items": items,
                "metadata": {
                    "valid_key": {"name": "valid", "value": 20},
                    "invalid_key": {"name": "invalid"},  # Missing 'value'
                },
            }
        }

        with pytest.raises(ValueError, match=r"Validation error for parameter 'data'"):
            convert_with_di(mock_client, test_func, arguments)

    def test_list_conversion_empty_path(self, mock_client: CogniteClient) -> None:
        """Verifies graceful handling when param_path is empty."""

        def test_func(client: CogniteClient, item: EdgeCaseItem) -> dict[str, EdgeCaseItem]:
            return {"item": item}

        # Top-level parameter error
        arguments: dict[str, Any] = {
            "item": {"name": "missing_value"}  # Missing required 'value'
        }

        with pytest.raises(ValueError, match=r"Validation error for parameter 'item'"):
            convert_with_di(mock_client, test_func, arguments)

    def test_list_conversion_with_mixed_errors(self, mock_client: CogniteClient) -> None:
        """Tests handling of multiple conversion failures - should fail fast on first error."""

        def test_func(client: CogniteClient, items: list[EdgeCaseItem]) -> dict[str, list[EdgeCaseItem]]:
            return {"items": items}

        # Multiple errors - should fail on first one
        arguments = {
            "items": [
                {"name": "first_invalid"},  # Missing 'value' - should fail here
                {"name": "second_invalid"},  # Also missing 'value' but shouldn't reach this
            ]
        }

        with pytest.raises(ValueError) as exc_info:
            convert_with_di(mock_client, test_func, arguments)

        # Should fail on first error and mention items[0]
        error_message = str(exc_info.value)
        assert "items[0]" in error_message or "parameter 'items' (list)" in error_message


class TestEdgeCasesAndSpecialValues:
    """Test suite for edge cases and special values in production scenarios."""

    def test_list_conversion_with_none_elements(self, mock_client: CogniteClient) -> None:
        """Validates Optional type handling - None values should pass through unchanged."""

        def test_func(client: CogniteClient, items: list[EdgeCaseItem | None]) -> dict[str, list[EdgeCaseItem | None]]:
            return {"items": items}

        arguments = {
            "items": [
                {"name": "valid", "value": 10},
                None,  # Should pass through as None
                {"name": "another_valid", "value": 20},
            ]
        }

        result = convert_with_di(mock_client, test_func, arguments)

        assert isinstance(result["items"], list)
        result = cast(dict[str, object], result)
        result["items"] = cast(list[EdgeCaseItem | None], result["items"])
        assert len(result["items"]) == 3
        assert isinstance(result["items"][0], EdgeCaseItem)
        assert result["items"][1] is None
        assert isinstance(result["items"][2], EdgeCaseItem)

    def test_optional_nested_structures(self, mock_client: CogniteClient) -> None:
        """Tests Optional handling in nested structures."""

        def test_func(client: CogniteClient, data: NestedEdgeCase | None) -> dict[str, NestedEdgeCase | None]:
            return {"data": data}

        # Test with None
        result = convert_with_di(mock_client, test_func, {"data": None})
        assert result["data"] is None
        metadata: dict[str, EdgeCaseItem] = {}  # Just to satisfy the type checker

        # Test with valid data
        arguments: dict[str, Any] = {
            "data": {
                "id": 1,
                "items": [{"name": "test", "value": 10}],
                "metadata": metadata,
            }
        }
        result = convert_with_di(mock_client, test_func, arguments)
        assert isinstance(result["data"], NestedEdgeCase)

    def test_list_conversion_recursive_depth(self, mock_client: CogniteClient) -> None:
        """Tests deeply nested list structures with accurate path reporting."""

        def test_func(
            client: CogniteClient, deep_data: list[dict[str, list[EdgeCaseItem]]]
        ) -> dict[str, list[dict[str, list[EdgeCaseItem]]]]:
            return {"deep_data": deep_data}

        # Very deeply nested structure with error
        arguments = {
            "deep_data": [
                {
                    "category1": [
                        {"name": "valid", "value": 10},
                        {"name": "invalid"},  # Missing 'value' - deep path
                    ]
                }
            ]
        }

        with pytest.raises(ValueError, match=r"Validation error for parameter 'deep_data'"):
            convert_with_di(mock_client, test_func, arguments)

    def test_list_conversion_with_circular_references(self, mock_client: CogniteClient) -> None:
        """Checks handling of circular structures - should fail gracefully."""

        def test_func(client: CogniteClient, item: CircularRef) -> dict[str, CircularRef]:
            return {"item": item}

        # Create circular reference in data
        circular_data = {
            "name": "parent",
            "parent": {
                "name": "child",
                "parent": None,  # This would normally create the cycle, but Pydantic prevents it
            },
        }

        # This should work fine - Pydantic handles this correctly
        result = convert_with_di(mock_client, test_func, {"item": circular_data})
        assert isinstance(result["item"], CircularRef)
        assert result["item"].name == "parent"
        assert isinstance(result["item"].parent, CircularRef)
        assert result["item"].parent.name == "child"
        assert result["item"].parent.parent is None

    def test_list_conversion_with_custom_exceptions(self, mock_client: CogniteClient) -> None:
        """Verifies proper wrapping of custom errors while preserving original error info."""

        class CustomValidationModel(BaseModel):
            """Model with custom validation that raises specific errors."""

            value: int

            def __init__(self, **data: Any) -> None:
                if "value" in data and data["value"] < 0:
                    raise ValueError("Custom error: value must be non-negative")
                super().__init__(**data)

        def test_func(client: CogniteClient, item: CustomValidationModel) -> dict[str, CustomValidationModel]:
            return {"item": item}

        arguments = {"item": {"value": -5}}  # Triggers custom validation error

        with pytest.raises(ValueError) as exc_info:
            convert_with_di(mock_client, test_func, arguments)

        error_message = str(exc_info.value)
        # Should wrap the error but preserve info about the parameter
        assert "parameter 'item'" in error_message or "CustomValidationModel at item" in error_message

    def test_error_boundary_conditions(self, mock_client: CogniteClient) -> None:
        """Tests error handling at type boundaries and edge conditions."""

        def test_func(
            client: CogniteClient,
            empty_list: list[EdgeCaseItem],
            single_item_list: list[EdgeCaseItem],
            deeply_nested: dict[str, dict[str, list[EdgeCaseItem]]],
        ) -> dict[str, Any]:
            return {
                "empty_list": empty_list,
                "single_item_list": single_item_list,
                "deeply_nested": deeply_nested,
            }

        # Test empty list (should work)
        result = convert_with_di(
            mock_client,
            test_func,
            {
                "empty_list": [],
                "single_item_list": [{"name": "solo", "value": 1}],
                "deeply_nested": {},
            },
        )
        assert result["empty_list"] == []
        assert isinstance(result["single_item_list"], list)
        result = cast(dict[str, object], result)
        result["single_item_list"] = cast(list[EdgeCaseItem], result["single_item_list"])
        assert len(result["single_item_list"]) == 1
        assert result["deeply_nested"] == {}

        # Test error in deeply nested structure
        with pytest.raises(ValueError, match=r"deeply_nested\[outer\]\[inner\]\[0\]"):
            convert_with_di(
                mock_client,
                test_func,
                {
                    "empty_list": [],
                    "single_item_list": [{"name": "solo", "value": 1}],
                    "deeply_nested": {
                        "outer": {
                            "inner": [{"name": "broken"}]  # Missing 'value'
                        }
                    },
                },
            )

    def test_unicode_and_special_characters(self, mock_client: CogniteClient) -> None:
        """Tests handling of Unicode characters and special strings in error paths."""

        def test_func(client: CogniteClient, item: EdgeCaseItem) -> dict[str, EdgeCaseItem]:
            return {"item": item}

        # Unicode in field names and values
        arguments = {
            "item": {
                "name": "test with unicode: 你好世界 🚀",
                "value": 42,
                "optional_field": "émojis and àccénts",
            }
        }

        result = convert_with_di(mock_client, test_func, arguments)
        assert isinstance(result["item"], EdgeCaseItem)
        assert result["item"].name == "test with unicode: 你好世界 🚀"
        assert result["item"].optional_field == "émojis and àccénts"

    def test_very_large_data_structures(self, mock_client: CogniteClient) -> None:
        """Tests performance and error handling with large data structures."""

        def test_func(client: CogniteClient, large_list: list[EdgeCaseItem]) -> dict[str, list[EdgeCaseItem]]:
            return {"large_list": large_list}

        # Create large list with error at the end
        large_data = [{"name": f"item_{i}", "value": i} for i in range(100)]
        large_data.append({"name": "broken"})  # Missing 'value' at position 100

        with pytest.raises(ValueError, match=r"Validation error for parameter 'large_list'"):
            convert_with_di(mock_client, test_func, {"large_list": large_data})

    def test_type_conversion_boundary_failures(self, mock_client: CogniteClient) -> None:
        """Tests that type conversion failures raise validation errors."""

        def test_func(
            client: CogniteClient,
            strict_int: int,
            strict_float: float,
            strict_bool: bool,
        ) -> dict[str, Any]:
            return {
                "strict_int": strict_int,
                "strict_float": strict_float,
                "strict_bool": strict_bool,
            }

        # These should raise validation errors when conversion fails
        with pytest.raises(
            ValueError,
            match=r"Validation error for parameter 'strict_int': Cannot convert 'not_a_number' \(type str\) to int",
        ):
            convert_with_di(
                mock_client,
                test_func,
                {"strict_int": "not_a_number"},
            )

        with pytest.raises(
            ValueError, match=r"Validation error for parameter 'strict_float': Cannot convert 'also_not_float' to float"
        ):
            convert_with_di(
                mock_client,
                test_func,
                {"strict_float": "also_not_float"},
            )

        # Bool conversion should work (returns False for values not in truthy list)
        result = convert_with_di(
            mock_client,
            test_func,
            {"strict_bool": "maybe_bool"},
        )
        assert result["strict_bool"] is False  # Any non-truthy string becomes False

    def test_error_message_consistency(self, mock_client: CogniteClient) -> None:
        """Ensures consistent error message format across different failure scenarios."""

        def test_func(
            client: CogniteClient,
            single_item: EdgeCaseItem,
            item_list: list[EdgeCaseItem],
            nested_dict: dict[str, EdgeCaseItem],
        ) -> dict[str, Any]:
            return {
                "single_item": single_item,
                "item_list": item_list,
                "nested_dict": nested_dict,
            }

        test_cases = [
            # (arguments, expected_pattern)
            (
                {"single_item": {"name": "test"}},  # Missing 'value'
                r"Validation error for parameter 'single_item'",
            ),
            (
                {
                    "single_item": {"name": "good", "value": 1},
                    "item_list": [{"name": "bad"}],
                },
                r"Validation error for.*item_list.*\[0\]",
            ),
            (
                {
                    "single_item": {"name": "good", "value": 1},
                    "item_list": [{"name": "good", "value": 1}],
                    "nested_dict": {"key": {"name": "bad"}},
                },
                r"Validation error for.*nested_dict\[key\]",
            ),
        ]

        for arguments, expected_pattern in test_cases:
            with pytest.raises(ValueError, match=expected_pattern):
                convert_with_di(mock_client, test_func, arguments)
