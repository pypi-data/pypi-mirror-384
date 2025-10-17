"""Type conversion utilities for Cognite Functions with FastAPI-style type safety.

## Problem Statement

Standard Cognite Functions receive untyped dictionary data and require manual parameter
validation and conversion. This creates several challenges:

- **Manual type conversion**: Developers must manually parse and validate each parameter
- **Error-prone**: String-to-type conversions are scattered throughout code
- **No introspection**: Functions become "black boxes" with unknown parameter requirements
- **Complex nested types**: Handling Optional, Union, and nested BaseModel types is cumbersome
- **Inconsistent validation**: Each function implements its own validation logic

## Solution Architecture

This module provides a **recursive type converter** that bridges the gap between untyped
Cognite Function inputs and strongly-typed Python function signatures. The architecture
consists of three main components:

### 1. Core Recursive Converter (`convert_value_to_type`)

The heart of the system - recursively converts any value to match a target type:

- **Basic types**: str → int/float/bool with proper parsing
- **Pydantic models**: dict → BaseModel with full validation
- **Collections**: Handles list[T] and dict[K, V] with recursive element conversion
- **Union types**: Attempts each type in order, including Optional[T]
- **Nested combinations**: Arbitrarily deep nesting like dict[str, list[BaseModel]]

### 2. Function Signature Integration (`convert_argument_to_typed_param`)

Bridges function introspection with type conversion:

- Extracts type hints from function signatures using `inspect` and `typing`
- Applies conversions only to parameters present in the function signature
- Preserves non-signature parameters unchanged for backward compatibility

### 3. Complete Argument Processing (`convert_arguments_to_typed_params`)

Main entry point that processes all function arguments:

- Adds required CogniteClient parameter automatically
- Converts all provided arguments based on function signature
- Handles default parameter values from function definitions
- Provides comprehensive error handling with parameter path information

## Key Features

### Recursive Type Support
Handles arbitrarily nested type combinations:
```python
dict[str, Optional[list[BaseModel]]]  # Deep nesting
Union[BaseModel, str, None]           # Multi-type unions
list[dict[str, BaseModel]]            # Collections of complex types
```

### Error Path Tracking
Provides precise error locations for debugging:
```python
# Error: "Validation error for BaseModel at users[0].address.street: field required"
```

### Type Annotation Compatibility
Supports both legacy and modern Python type syntax:
```python
Union[User, None]  # Legacy, but still used in newer versions of Python
User | None        # Modern (Python 3.10+)
```

### Backward Compatibility
- Unknown parameters pass through unchanged
- Functions without type hints use original data
- Graceful degradation for complex type introspection failures

This architecture enables the FastAPI-style developer experience where complex nested
data structures are automatically validated and converted, eliminating the need for
manual parameter processing in Cognite Functions.
"""

import inspect
import types
import warnings
from collections.abc import Callable
from typing import Any, Union, cast, get_args, get_origin, get_type_hints

from cognite.client import CogniteClient
from pydantic import BaseModel

from .logger import get_function_logger
from .models import DataDict, FunctionCallInfo, SecretsMapping, TypedParam, TypedResponse

UnionTypes = (Union, types.UnionType)


class ConvertError(ValueError):
    """Exception raised when parameter conversion/validation fails.

    This allows us to distinguish between validation errors (which should be
    classified as ValidationError) and execution errors from user functions
    (which should be classified as ExecutionError).
    """


# Boolean conversion constants
TRUTHY_STRING_VALUES = ("true", "1", "yes", "on")


def convert_value_to_type(value: Any, target_type: type[Any], param_path: str = "") -> Any | None:
    """Recursively convert a value to match a target type.

    Args:
        value: The value to convert
        target_type: The target type to convert to
        param_path: Path for error reporting (e.g., "param.field[0]")

    Returns:
        The converted value matching the target type
    """
    # Handle None values and Optional types
    if value is None:
        return None

    # Get type origin and arguments
    origin: type[Any] | None = get_origin(target_type)
    generic_args: tuple[type[Any], ...] = get_args(target_type)

    # Handle direct type matches first
    if target_type is type(value):
        return value

    # Handle Union types (including Optional which is Union[T, None])
    # Also handle modern union syntax (X | Y) which creates types.UnionType in Python 3.10+
    if origin in UnionTypes:
        # For Union types, try each type in order
        if generic_args:
            # Handle Optional[T] (which is Union[T, None])
            non_none_types = [t for t in generic_args if t is not type(None)]
            if len(non_none_types) == 1 and type(None) in generic_args:
                # This is Optional[T], convert to T if not None
                if value is None:
                    return None
                return convert_value_to_type(value, non_none_types[0], param_path)

            # For other Union types, try each type until one works
            last_error: Exception | None = None
            for union_type in generic_args:
                if union_type is type(None) and value is None:
                    return None
                try:
                    return convert_value_to_type(value, union_type, param_path)
                except Exception as e:
                    last_error = e
                    continue

            # If we get here, none of the union types worked
            if last_error:
                raise ConvertError(f"Could not convert value to any type in Union at {param_path}: {last_error}")

    # Handle Pydantic BaseModel
    if inspect.isclass(target_type) and issubclass(target_type, BaseModel):
        if isinstance(value, dict):
            try:
                return target_type(**value)
            except Exception as e:
                # Use different error message formats for top-level vs nested parameters
                if param_path and "[" not in param_path:
                    # Top-level parameter
                    raise ConvertError(f"Validation error for parameter '{param_path}': {e!s}") from e

                # Nested parameter
                raise ConvertError(f"Validation error for {target_type.__name__} at {param_path}: {e}") from e
        if isinstance(value, target_type):
            return value

        raise ConvertError(f"Cannot convert {type(value)} to {target_type.__name__} at {param_path}")

    # Handle list types. Note that Python's type introspection treats
    # legacy and modern collection syntax identically.
    if origin is list:
        if not isinstance(value, list):
            raise ConvertError(f"Expected list but got {type(value)} at {param_path}")

        if not generic_args:
            warnings.warn(f"Untyped list at {param_path}, returning as-is")
            return value  # type: ignore # Untyped list, return as-is

        element_type = generic_args[0]
        try:
            return [
                convert_value_to_type(item, element_type, f"{param_path}[{i}]")
                for i, item in enumerate(cast(list[Any], value))
            ]
        except Exception as e:
            # Use different error message formats for top-level vs nested parameters
            if param_path and "[" not in param_path:
                # Top-level parameter
                raise ConvertError(f"Validation error for parameter '{param_path}' (list): {e!s}") from e
            # Nested parameter
            raise ConvertError(f"List conversion error at {param_path}: {e}") from e

    # Handle dict types. Python's type introspection treats legacy and
    # modern collection syntax identically:
    if origin is dict:
        if not isinstance(value, dict):
            raise ConvertError(f"Expected dict but got {type(value)} at {param_path}")

        if len(generic_args) != 2:
            warnings.warn(f"Untyped dict at {param_path}, returning as-is")
            return value  # type: ignore # Untyped dict, return as-is

        key_type, value_type = generic_args
        try:
            return {
                convert_value_to_type(k, key_type, f"{param_path}.key"): convert_value_to_type(
                    v, value_type, f"{param_path}[{k}]"
                )
                for k, v in cast(dict[str, Any], value).items()
            }
        except Exception as e:
            raise ConvertError(f"Dict conversion error at {param_path}: {e}") from e

    # Handle basic type conversions for strings
    if isinstance(value, str) and target_type is not str:
        try:
            if target_type is int and value.lstrip("-").isdigit():
                return int(value)
            if target_type is float:
                return float(value)
            if target_type is bool:
                return value.lower() in TRUTHY_STRING_VALUES
        except (ValueError, AttributeError) as e:
            # Raise validation error for failed type conversion
            if param_path and "[" not in param_path:
                # Top-level parameter
                msg = (
                    f"Validation error for parameter '{param_path}': Cannot convert '{value}' to {target_type.__name__}"
                )
                raise ConvertError(msg) from e
            else:
                # Nested parameter
                msg = f"Type conversion error at {param_path}: Cannot convert '{value}' to {target_type.__name__}"
                raise ConvertError(msg) from e

    # For other types, check if value is compatible with target type
    if isinstance(value, target_type):
        return value

    # If we can't convert to the target type, raise validation error. Keeping
    # separate from error handling above. Looks similar, but different failure
    # modes.
    if param_path and "[" not in param_path:
        # Top-level parameter
        msg = (
            f"Validation error for parameter '{param_path}': Cannot convert '{value}' "
            f"(type {type(value).__name__}) to {target_type.__name__}"
        )
        raise ConvertError(msg)
    # Nested parameter
    msg = (
        f"Type conversion error at {param_path}: Cannot convert '{value}' "
        f"(type {type(value).__name__}) to {target_type.__name__}"
    )
    raise ConvertError(msg)


def convert_argument_to_typed_param(
    param_name: str,
    param_value: TypedParam,
    sig: inspect.Signature,
    type_hints: dict[str, type],
) -> TypedParam:
    """Convert a single argument to a properly typed parameter based on function signature."""
    if param_name not in sig.parameters or param_name not in type_hints:
        # Parameter not in signature, return as-is
        return param_value

    param_type = type_hints[param_name]

    # Use the recursive conversion function
    return convert_value_to_type(param_value, param_type, param_name)


def convert_arguments_to_typed_params(
    client: CogniteClient,
    func: Callable[..., TypedResponse],
    arguments: DataDict,
    secrets: SecretsMapping | None = None,
    function_call_info: FunctionCallInfo | None = None,
) -> dict[str, TypedParam]:
    """Convert dict arguments to properly typed parameters based on function signature.

    This function implements dependency injection for Cognite Function dependencies:
    - client: CogniteClient instance
    - secrets: Optional secrets mapping
    - function_call_info: Optional function call metadata
    - logger: Isolated logger instance for the function

    These dependencies are only added if the function explicitly declares them as parameters.
    """
    kwargs: dict[str, TypedParam] = {}

    try:
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)
    except (ValueError, NameError, AttributeError):
        # If we can't get type hints, add client and arguments directly (backward compatibility)
        func_name = getattr(func, "__name__", str(func))
        warnings.warn(f"Could not get type hints for function {func_name}, adding arguments directly")
        kwargs["client"] = client
        kwargs.update(arguments)
        return kwargs

    # Dependency injection: Add dependencies only if declared in function signature
    if "client" in sig.parameters:
        kwargs["client"] = client
    if "secrets" in sig.parameters:
        kwargs["secrets"] = secrets or {}
    if "function_call_info" in sig.parameters:
        kwargs["function_call_info"] = function_call_info
    if "logger" in sig.parameters:
        kwargs["logger"] = get_function_logger()

    # Convert arguments based on function signature and type hints
    for param_name, param_value in arguments.items():
        kwargs[param_name] = convert_argument_to_typed_param(param_name, param_value, sig, type_hints)

    # Handle function default parameters that weren't provided in arguments
    for param_name, param in sig.parameters.items():
        # Skip dependency injection parameters - they're handled above
        if param_name in ("client", "secrets", "function_call_info", "logger"):
            continue
        if param_name not in kwargs:
            if param.default != inspect.Parameter.empty:
                kwargs[param_name] = param.default
            # If parameter is missing and has no default, Python will raise TypeError when called

    return kwargs
