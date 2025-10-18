"""Tests for text formatting utilities."""

from cognite_typed_functions.formatting import format_tool_name
from cognite_typed_functions.models import HTTPMethod


class TestFormatToolName:
    """Test the format_tool_name function."""

    def test_tool_name_generation_basic(self) -> None:
        """Test basic tool name generation from paths and methods."""
        test_cases = [
            ("/items/", "POST", "test_app_post_items"),
            ("/items/{item_id}", "GET", "test_app_get_items_by_item_id"),
            ("/", "GET", "test_app_get_root"),
            ("/user/profile", "PUT", "test_app_put_user_profile"),
            (
                "/complex-path/sub_path/{id}/edit",
                "POST",
                "test_app_post_complex_path_sub_path_by_id_edit",
            ),
        ]

        for path, method, expected in test_cases:
            result = format_tool_name(path, HTTPMethod(method), "Test App")
            assert result == expected, f"Path: {path}, Method: {method}"

    def test_tool_name_prefix_normalization(self) -> None:
        """Test that prefixes are properly normalized."""
        test_cases = [
            ("Customer Portal", "customer_portal"),
            ("My API v2.0", "my_api_v2_0"),
            ("Product-Catalog", "product_catalog"),
            ("API_Service", "api_service"),
            ("Service@Company.com", "service_company_com"),
            ("1st App", "app_1st_app"),  # Leading number
            ("123Service", "app_123service"),  # Leading number
            ("", ""),  # Empty prefix
            ("   ", ""),  # Whitespace only
            ("Test!", "test"),  # Special chars removed
        ]

        for prefix, expected_normalized in test_cases:
            result = format_tool_name("/test", HTTPMethod.GET, prefix)
            if expected_normalized:
                assert result.startswith(expected_normalized + "_")
            else:
                assert result == "get_test"

    def test_tool_name_no_prefix(self) -> None:
        """Test tool name generation without prefix."""
        test_cases = [
            ("/items/", "POST", "post_items"),
            ("/items/{item_id}", "GET", "get_items_by_item_id"),
            ("/", "GET", "get_root"),
            ("/user/profile", "PUT", "put_user_profile"),
        ]

        for path, method, expected in test_cases:
            result = format_tool_name(path, HTTPMethod(method), "")
            assert result == expected, f"Path: {path}, Method: {method}"

    def test_tool_name_empty_path_segments(self) -> None:
        """Test tool name generation with empty path segments."""
        test_cases = [
            ("///", "GET", "get_root"),
            ("/items//", "POST", "post_items"),
            ("//items/{id}//", "GET", "get_items_by_id"),
        ]

        for path, method, expected in test_cases:
            result = format_tool_name(path, HTTPMethod(method), "")
            assert result == expected, f"Path: {path}, Method: {method}"

    def test_tool_name_parameter_formatting(self) -> None:
        """Test parameter formatting in tool names."""
        test_cases = [
            ("/users/{user_id}", "GET", "get_users_by_user_id"),
            ("/orders/{order_id}/items/{item_id}", "POST", "post_orders_by_order_id_items_by_item_id"),
            ("/{id}", "DELETE", "delete_by_id"),
            ("/files/{file_id}/download", "GET", "get_files_by_file_id_download"),
        ]

        for path, method, expected in test_cases:
            result = format_tool_name(path, HTTPMethod(method), "")
            assert result == expected, f"Path: {path}, Method: {method}"

    def test_tool_name_method_cases(self) -> None:
        """Test that HTTP methods are properly lowercased."""
        test_cases = [
            ("GET", "get"),
            ("POST", "post"),
            ("PUT", "put"),
            # ("PATCH", "patch"),
            ("DELETE", "delete"),
        ]

        for method, expected_method in test_cases:
            result = format_tool_name("/test", HTTPMethod(method), "")
            assert result == f"{expected_method}_test"

    def test_tool_name_embedded_parameters(self) -> None:
        """Test parameter extraction from embedded parameters in path segments."""
        test_cases = [
            ("/items/item_{id}", "GET", "get_items_item_by_id"),
            ("/users/user_{user_id}/profile", "PUT", "put_users_user_by_user_id_profile"),
            ("/api/v{version}/data", "GET", "get_api_v_by_version_data"),
            ("/files/{type}_{id}.json", "POST", "post_files_by_type_by_id_json"),
            ("/logs/app_{app_id}_log_{log_id}", "DELETE", "delete_logs_app_by_app_id_log_by_log_id"),
            ("/prefix{id}suffix", "GET", "get_prefix_by_id_suffix"),
            ("/{id}{id}", "GET", "get_by_id_by_id"),
        ]

        for path, method, expected in test_cases:
            result = format_tool_name(path, HTTPMethod(method), "")
            assert result == expected, f"Path: {path}, Method: {method}, Got: {result}, Expected: {expected}"

    def test_tool_name_adjacent_identical_parameters(self) -> None:
        """Test that adjacent identical parameters are handled correctly."""
        test_cases = [
            ("/{id}{id}", "GET", "get_by_id_by_id"),
            ("/prefix{id}{id}suffix", "POST", "post_prefix_by_id_by_id_suffix"),
            ("/{type}_{type}/{id}", "PUT", "put_by_type_by_type_by_id"),
            ("/api/v{version}_{version}", "DELETE", "delete_api_v_by_version_by_version"),
        ]

        for path, method, expected in test_cases:
            result = format_tool_name(path, HTTPMethod(method), "")
            assert result == expected, f"Path: {path}, Method: {method}, Got: {result}, Expected: {expected}"
