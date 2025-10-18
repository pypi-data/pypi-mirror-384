"""Cross-cutting types and models for Cognite Functions.

This module contains types, protocols, and models that are shared across
multiple components of the framework. It focuses on cross-cutting concerns
rather than module-specific implementations.

Core Framework Types:
    - JSONLike, DataDict, TypedParam, TypedResponse: Universal data types
    - Handler: Protocol definition for traditional function handlers
    - RouteHandler: Type alias for flexible route handler functions
    - HTTPMethod: Shared enumeration for HTTP operations

Cognite Integration:
    - FunctionCallInfo: Cognite-specific metadata for function calls
    - CogniteTypedError, CogniteTypedResponse: Standardized response formats
    - RequestData: Parsed request data structure

Design Philosophy:
    This module serves as the "shared vocabulary" of the framework, containing
    types that need to be consistent across routing, application logic, and
    response handling. Module-specific types (like RouteInfo) belong in their
    respective modules to maintain clear boundaries and reduce coupling.
"""

from collections.abc import Awaitable, Callable, Mapping, Sequence
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, TypeAlias, TypedDict
from urllib.parse import parse_qs, urlparse

from cognite.client import CogniteClient
from pydantic import BaseModel, Field
from typing_extensions import TypeAliasType


# Exception hierarchy for framework-specific errors
class CogniteTypedFunctionsError(Exception):
    """Base exception for all Cognite Typed Functions framework errors.

    This base class allows callers to catch all framework-specific errors
    while still being able to distinguish between different error types
    using more specific subclasses.
    """

    pass


class ConfigurationError(CogniteTypedFunctionsError):
    """Exception raised when there is a configuration error in the framework.

    This includes errors such as:
    - Invalid dependency registrations
    - Path parameter conflicts with dependencies
    - Invalid route configurations
    - Other setup/configuration issues that should be caught during development

    These errors indicate problems with how the framework is configured,
    not runtime errors from user requests.
    """

    pass


class FunctionCallInfo(TypedDict):
    """Function call information."""

    function_id: str
    call_id: str

    # If the call is scheduled
    schedule_id: str | None
    scheduled_time: str | None


if TYPE_CHECKING:
    # Recursive types for type checking (pyright). These work with pyright, but not for Pydantic (RecursionError)
    Json: TypeAlias = Mapping[str, "Json"] | Sequence["Json"] | str | int | float | bool | None
    TypedResponse: TypeAlias = (
        BaseModel | Sequence["TypedResponse"] | Mapping[str, "TypedResponse"] | str | int | float | bool | None
    )

else:
    # Recursive types for runtime (Pydantic)
    # These work for Pydantic, but not with pyright. Note the use of `Mapping` and
    # `Sequence` to make them covariant. For more information, see
    # https://docs.pydantic.dev/2.11/concepts/types/#named-recursive-types
    Json = TypeAliasType(
        "Json",
        "Mapping[str, Json] | Sequence[Json] | str | int | float | bool | None",
    )
    TypedResponse = TypeAliasType(
        "TypedResponse",
        "BaseModel | Sequence[TypedResponse] | Mapping[str, TypedResponse] | str | int | float | bool | None",
    )


# Type aliases for better readability
DataDict: TypeAlias = Mapping[str, Json]
SecretsMapping: TypeAlias = Mapping[str, str]


class HTTPMethod(str, Enum):
    """HTTP methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"

    def __str__(self) -> str:
        """Return the string value of the HTTP method."""
        return self.value


class Handle(Protocol):
    """Handler function type.

    This is the traditional function handler type used in Cognite Functions.
    """

    def __call__(
        self,
        *,
        client: CogniteClient,
        data: DataDict,
        secrets: SecretsMapping | None = None,
        function_call_info: FunctionCallInfo | None = None,
    ) -> Json:
        """Call the handler."""
        ...


class FunctionService:
    """Type-safe wrapper for Cognite Function services.

    This class provides both synchronous and asynchronous handle functions
    for Cognite Functions, enabling type-safe access to the async implementation
    for devserver optimization.

    The instance is callable and implements the Handle protocol for compatibility
    with the Cognite Functions runtime.

    Attributes:
        async_handle: The async implementation for optimal devserver performance
    """

    def __init__(
        self,
        sync_handle: Handle,
        async_handle: Callable[..., Awaitable[DataDict]],
    ):
        """Initialize the FunctionService.

        Args:
            sync_handle: The synchronous handle function
            async_handle: The asynchronous handle function
        """
        self._sync_handle = sync_handle
        self.async_handle = async_handle

    def __call__(
        self,
        *,
        client: CogniteClient,
        data: DataDict,
        secrets: SecretsMapping | None = None,
        function_call_info: FunctionCallInfo | None = None,
    ) -> Json:
        """Call the synchronous handle (Handle protocol implementation).

        This makes FunctionService callable and compatible with the Cognite
        Functions runtime expectations.

        Args:
            client: The Cognite client instance
            data: Request data containing path, method, and body
            secrets: Optional secrets mapping
            function_call_info: Optional function call metadata

        Returns:
            Response data dict
        """
        return self._sync_handle(
            client=client,
            data=data,
            secrets=secrets,
            function_call_info=function_call_info,
        )


class CogniteTypedError(BaseModel):
    """Structured error response."""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": False,
                    "error_type": "ValidationError",
                    "message": "Invalid input data",
                    "details": {"field": "value"},
                }
            ]
        }
    }

    success: bool = False
    error_type: str
    message: str
    details: Mapping[str, Any] | None = None


class CogniteTypedResponse(BaseModel):
    """Wrapper for successful responses."""

    model_config = {"json_schema_extra": {"examples": [{"success": True, "data": {"result": "example response"}}]}}

    success: bool = True
    data: TypedResponse


class RequestData(BaseModel):
    """Parsed request data from a Cognite Function call."""

    path: str = "/"
    """Raw path with query string (e.g., "/items/123?include_tax=true")"""
    method: HTTPMethod = HTTPMethod.POST
    """HTTP method (GET, POST, etc.)"""
    body: Mapping[str, Any] = Field(default_factory=dict)
    """Request body data"""

    # Computed fields that are parsed from path
    clean_path: str = ""
    """Just the path part (e.g., "/items/123")"""
    query: Mapping[str, str | Sequence[str]] = Field(default_factory=dict)
    """Parsed query parameters"""

    def model_post_init(self, __context: Any) -> None:
        """Parse path and query string after Pydantic validation."""
        # Parse the full path to extract clean path and query params
        parsed = urlparse(self.path)

        # Set the clean path (without query string)
        self.clean_path = parsed.path or "/"

        # Parse query parameters
        query_params = parse_qs(parsed.query)
        query: dict[str, str | list[str]] = {}
        for key, value_list in query_params.items():
            if len(value_list) == 1:
                query[key] = value_list[0]
            else:
                query[key] = value_list  # Keep as list if multiple values

        self.query = query
