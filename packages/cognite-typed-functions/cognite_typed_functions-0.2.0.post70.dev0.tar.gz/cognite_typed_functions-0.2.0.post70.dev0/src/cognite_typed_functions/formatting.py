"""Text formatting utilities for Cognite Functions.

This module contains functions for processing and formatting text content,
particularly for external integrations like MCP tools.
"""

import re

from cognite_typed_functions.models import HTTPMethod


def format_tool_name(path: str, method: HTTPMethod, prefix: str = "") -> str:
    """Format route information into a valid MCP tool name.

    Converts HTTP route paths and methods into valid identifier names suitable
    for MCP tool names. Uses regex-based parameter extraction to handle both
    standard path parameters and embedded parameters within path segments.

    The function performs the following transformations:
    - Extracts path parameters using regex pattern matching
    - Replaces {param} with "by_param" format
    - Adds word separators when parameters are adjacent to other characters
    - Normalizes special characters (dots, hyphens) to underscores
    - Combines method, path, and optional prefix into a valid identifier

    Args:
        path: The route path pattern. Supports both standard parameters like
              '/items/{item_id}' and embedded parameters like '/api/v{version}/data'
        method: The HTTP method (GET, POST, PUT, DELETE)
        prefix: Optional prefix for the tool name (e.g., app name). Will be
                normalized to a valid identifier format.

    Returns:
        A valid Python identifier suitable for use as an MCP tool name.

    Examples:
        >>> format_tool_name('/items/{id}', HTTPMethod.GET, 'my_app')
        'my_app_get_items_by_id'

        >>> format_tool_name('/api/v{version}/data', HTTPMethod.POST, '')
        'post_api_v_by_version_data'

        >>> format_tool_name('/files/{type}_{id}.json', HTTPMethod.GET, '')
        'get_files_by_type_by_id_json'

        >>> format_tool_name('/prefix{id}suffix', HTTPMethod.DELETE, '')
        'delete_prefix_by_id_suffix'
    """
    method_lower = method.lower()

    # Transform parameters into semantic tool name components (e.g., {id} becomes "by_id")
    def replacement_func(match: re.Match[str]) -> str:
        param_name = match.group(1)
        start_pos = match.start()
        end_pos = match.end()

        # Check against the original path string for word boundaries to correctly insert separators
        # for embedded parameters like "/api/v{version}" or "/prefix{id}suffix", and adjacent parameters like
        # "{id}{id}".
        needs_prefix_sep = start_pos > 0 and (path[start_pos - 1].isalnum() or path[start_pos - 1] == "}")
        needs_suffix_sep = end_pos < len(path) and (path[end_pos].isalnum() or path[end_pos] == "{")

        replacement = f"by_{param_name}"
        if needs_prefix_sep:
            replacement = f"_{replacement}"
        if needs_suffix_sep:
            replacement = f"{replacement}_"
        return replacement

    processed_path = re.sub(r"\{(\w+)\}", replacement_func, path)

    # Convert path segments into valid Python identifier components
    path_parts = processed_path.strip("/").split("/")
    clean_parts: list[str] = []
    for part in path_parts:
        if not part:  # Avoid empty segments from paths like "//items/"
            continue
        # Replace non-alphanumeric characters with underscores to ensure compatibility with Python identifier rules
        # (dots, hyphens → underscores)
        cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", part)
        # Clean up multiple underscores to prevent awkward names like "api__v2__data" from multiple adjacent special
        # chars
        cleaned = re.sub(r"_+", "_", cleaned).strip("_")
        if cleaned:  # Avoid contributing empty strings to the final tool name
            clean_parts.append(cleaned)

    # Ensure app/service prefixes create valid Python identifiers
    normalized_prefix = ""
    if prefix and prefix.strip():
        # Replace any sequence of non-alphanumeric characters with a single underscore for consistent normalization.
        s = re.sub(r"[^a-z0-9]+", "_", prefix.lower()).strip("_")
        if s and s[0].isdigit():
            s = f"app_{s}"
        normalized_prefix = s

    # Build the tool name
    path_part = "_".join(clean_parts) if clean_parts else "root"

    name_parts = [part for part in [normalized_prefix, method_lower, path_part] if part]
    return "_".join(name_parts)
