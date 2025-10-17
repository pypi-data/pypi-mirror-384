"""Dependency injection system for Cognite Functions.

This module provides a flexible dependency injection system that allows the framework
to inject dependencies like CogniteClient, secrets, and logger into route endpoints,
while also allowing users to register their own custom dependencies.

The DI system follows these principles:
- Dependencies are only injected if explicitly declared in function signatures
- Type-safe: dependencies are resolved based on parameter types and optionally names
- Extensible: users can register custom dependency providers
- Framework-provided dependencies are registered by default

Matching Semantics (AND logic):
- Framework dependencies use name AND type matching for strict, predictable behavior
- User dependencies typically use type-only matching for flexible parameter naming
- Type is ALWAYS required (this is a typed functions framework)
- When both name and type are specified: BOTH must match (AND semantics)
- When only type is specified: only type must match (any name)

Current Limitations:
- Dependency chains between custom providers are NOT supported. All providers are
  resolved against the same initial context (client, secrets, function_call_info).
  A resolved dependency is not made available to other providers within the same
  resolution cycle.

  Example that will NOT work:
      registry.register(provider=lambda ctx: create_db(ctx["secrets"]),
                       target_type=Database)
      registry.register(provider=lambda ctx: UserRepo(db=ctx["db"]),  # KeyError!
                       target_type=UserRepository)

  Workaround: Resolve dependencies in multiple passes manually, or design providers
  to only depend on the initial context (client, secrets, function_call_info).

  Future: This could be addressed by implementing dependency graph resolution with
  topological sorting to resolve providers in the correct order.
"""

import inspect
import logging
import types
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, NamedTuple, TypeAlias, Union, get_args, get_origin

from cognite.client import CogniteClient

from .logger import get_function_logger
from .models import ConfigurationError, FunctionCallInfo, SecretsMapping

# Type aliases for improved readability
DependencyContext: TypeAlias = Mapping[str, object]
"""Dictionary mapping parameter names to dependency values."""
ProviderFunction: TypeAlias = Callable[[DependencyContext], object]
"""Callable that takes a context dictionary and returns the dependency value."""

# Union types - handles both old-style Union[X, Y] and new-style X | Y
UnionTypes = (Union, types.UnionType)


class DependencyInfo(NamedTuple):
    """Information about a registered dependency provider.

    Attributes:
        target_type: The type annotation that triggers this dependency
        param_name: Optional parameter name for stricter matching (None for type-only matching)
        description: Human-readable description of the dependency
    """

    target_type: type[Any]
    param_name: str | None
    description: str


# Types that are too generic for type-only dependency injection
# These can be used with name+type or name-only, but NOT with type-only matching
GENERIC_TYPES_REQUIRING_NAME: frozenset[type] = frozenset(
    {
        # Primitives
        str,
        int,
        float,
        bool,
        # Concrete collections
        list,
        dict,
        tuple,
        set,
        # Abstract collections
        Mapping,
        Sequence,
        # Special types
        type(None),
        object,
    }
)
"""Built-in types that are too generic for type-only dependency injection.

These types (including parameterized variants) would conflict with request parameters.
They can ONLY be used when a param_name is also specified to ensure precise matching.

Examples:
- ❌ register(provider, target_type=int) - Matches any int (path param, query param, etc.)
- ❌ register(provider, target_type=list[int]) - Matches any list[int] (e.g., query ?ids=1,2,3)
- ❌ register(provider, target_type=dict[str, str]) - Matches any dict[str, str] request body
- ✅ register(provider, target_type=int, param_name="max_retries") - Specific, only "max_retries"
- ✅ register(provider, target_type=Redis) - Custom class, clearly a dependency not request data

Note: Custom classes (Redis, Database, MyService) are always allowed for type-only matching
since they represent services/dependencies, not request data.
"""


@dataclass(frozen=True)
class DependencyProvider:
    """Wrapper for a single dependency provider function.

    Encapsulates a provider function along with matching criteria (param_name and/or type).
    The provider function is invoked via the resolve() method.

    Matching behavior (AND semantics):
    - If only target_type is specified: matches parameters with that type annotation (any param name)
    - If both param_name and target_type are specified: matches parameters with BOTH that param name
      AND that type (AND logic)

    Note: target_type is MANDATORY - this is a typed functions framework, all dependencies must have types.
    """

    provider: ProviderFunction
    target_type: Any
    param_name: str | None = None
    description: str = ""

    def __post_init__(self):
        """Validate dependency registration."""
        # Check if target_type is too generic for type-only matching
        # Generic types are only blocked when used WITHOUT a param_name
        if self.param_name is None and self._is_blocked_type(self.target_type):
            type_name = getattr(self.target_type, "__name__", str(self.target_type))
            raise ConfigurationError(
                f"Cannot register dependency with type-only matching for generic type '{type_name}'. "
                f"This type is too generic and would conflict with request parameters. "
                f"You must specify a 'param_name' along with the type to ensure precise matching "
                f"(e.g., param_name='max_retries', target_type=int), or use a custom class "
                f"(e.g., target_type=Redis, target_type=Database)."
            )

    @staticmethod
    def _is_blocked_type(target_type: Any) -> bool:
        """Check if a type is too generic for type-only matching.

        Blocks built-in types (bare or parameterized) that could conflict with request parameters:
        - Bare: str, int, list, dict, Mapping, typing.List, typing.Dict, etc.
        - Parameterized: list[int], dict[str, str], typing.List[str], Mapping[str, str], etc.

        These types are commonly used for request parameters (path, query, body) and would
        cause ambiguity if used for type-only dependency injection.

        Allows custom classes (e.g., Redis, Database, MyService) which are clearly dependencies.

        Args:
            target_type: The type or type annotation to check (can be type, GenericAlias, Union, etc.)

        Returns:
            True if the type should be blocked for type-only matching
        """
        origin = get_origin(target_type)

        # For parameterized types (e.g., list[int], typing.List[str]), check the origin
        # For bare types (e.g., list, int), check the type itself
        type_to_check = origin or target_type

        # Block if the base type is a generic built-in type
        # This blocks both bare (int, list) and parameterized (list[int], dict[str, str])
        # but allows custom classes (Redis, MyService, etc.)
        return type_to_check in GENERIC_TYPES_REQUIRING_NAME

    def matches(self, param_name: str, param: inspect.Parameter) -> bool:
        """Check if this provider matches the given parameter.

        AND semantics:
        - If only target_type is specified: only type must match (param name doesn't matter)
        - If both param_name and target_type are specified: BOTH must match

        Note: target_type is always specified (mandatory), param_name is optional.
        """
        # If param_name is specified but doesn't match, fail immediately
        if self.param_name is not None and self.param_name != param_name:
            return False

        # Check type match (target_type is always specified)
        type_matches = param.annotation != inspect.Parameter.empty and self._types_compatible(param.annotation)
        return type_matches

    def _is_subclass_safe(self, annotation_type: object) -> bool:
        """Safely check if target_type can be injected into a parameter with annotation_type.

        Handles TypeError exceptions that can occur with special typing constructs.

        Checks if the provider type is a subclass of (or equal to) the parameter type,
        following the Liskov Substitution Principle: a more specific type can be used
        wherever a more general type is expected.

        Examples:
        - Provider: Programmer, Parameter: Person → ✓ (Programmer is subclass of Person)
        - Provider: dict, Parameter: Mapping → ✓ (dict is subclass of Mapping)
        - Provider: Person, Parameter: Programmer → ✗ (Person is NOT subclass of Programmer)
        - Provider: Mapping, Parameter: dict → ✗ (cannot inject abstract into concrete)

        Args:
            annotation_type: The parameter's type annotation (what the function expects)

        Returns:
            True if target_type (what the provider provides) is compatible with annotation_type
        """
        try:
            if isinstance(self.target_type, type) and isinstance(annotation_type, type):
                return issubclass(self.target_type, annotation_type)
        except TypeError:
            # Some types can't be used with issubclass
            pass
        return False

    def _is_type_compatible_with_target(self, annotation: object) -> bool:
        """Check if an annotation is compatible with target_type via subclass or origin.

        Handles both bare types and parameterized types by checking:
        1. Direct subclass relationship with the annotation
        2. Subclass relationship with the origin of parameterized types

        Args:
            annotation: The type annotation to check (can be bare or parameterized)

        Returns:
            True if annotation is compatible with target_type
        """
        # Check subclass relationship with the annotation itself
        if self._is_subclass_safe(annotation):
            return True

        # Check parameterized types (e.g., dict[str, str] -> dict, Mapping[str, str] -> Mapping)
        origin = get_origin(annotation)
        if origin is not None:
            if self._is_subclass_safe(origin):
                return True

        return False

    def _is_union_member_compatible(self, origin: type[Any] | None, annotation: object) -> bool:
        """Check if target_type is compatible with any member of a Union type.

        Handles Union types like `Type | None` or `Optional[Type]` by checking if
        target_type matches any of the union members, including subclass relationships
        and parameterized types.

        Args:
            origin: The origin type (e.g., Union, types.UnionType)
            annotation: The type annotation to check

        Returns:
            True if target_type matches any union member, False otherwise
        """
        # Only process if it's actually a Union type
        if origin not in UnionTypes:
            return False

        args = get_args(annotation)
        if not args:
            return False

        for arg in args:
            # Direct match with union member
            if arg == self.target_type:
                return True

            # Check subclass relationships and parameterized types
            if self._is_type_compatible_with_target(arg):
                return True

        return False

    def _types_compatible(self, annotation: object) -> bool:
        """Check if the annotation is compatible with target_type.

        Handles direct matches, subclass relationships, Union types (e.g., Type | None),
        and parameterized types (e.g., dict[str, str]).
        """
        if annotation == self.target_type:
            return True

        # Handle Union types (e.g., FunctionCallInfo | None, Optional[Type])
        origin = get_origin(annotation)
        if origin is not None:
            if self._is_union_member_compatible(origin, annotation):
                return True

        # Handle subclasses and parameterized types (e.g., SecretsMapping, dict[str, str])
        if self._is_type_compatible_with_target(annotation):
            return True

        return False

    def resolve(self, context: DependencyContext) -> object:
        """Resolve the dependency using the provided context.

        Args:
            context: Context dictionary containing available values

        Returns:
            The resolved dependency value
        """
        return self.provider(context)


class DependencyRegistry:
    """Registry for managing dependency injection.

    The registry maintains a collection of dependency providers that can match
    parameters by name, type, or both using AND semantics. When resolving dependencies
    for a function, it only injects dependencies that are explicitly declared in the
    function's signature.

    Matching Logic (AND semantics):
    - Type is ALWAYS required (this is a typed functions framework)
    - Both name and type specified: parameter must match BOTH
    - Only type specified: parameter must match type (any name)

    Important Limitation:
        Dependency chains between custom providers are NOT currently supported.
        All providers resolve against the same initial context simultaneously.
        See module docstring for details and workarounds.
    """

    def __init__(self) -> None:
        """Initialize an empty dependency registry."""
        self._providers: list[DependencyProvider] = []

    @staticmethod
    def _has_same_matching_condition(provider1: DependencyProvider, provider2: DependencyProvider) -> bool:
        """Check if two providers have the same matching condition.

        Two providers have the same matching condition if they have the same
        param_name and target_type, meaning they would match the exact same parameters.

        Args:
            provider1: First provider to compare
            provider2: Second provider to compare

        Returns:
            True if both providers would match the same parameters
        """
        return provider1.param_name == provider2.param_name and provider1.target_type == provider2.target_type

    def register(
        self,
        provider: Callable[[Mapping[str, object]], object],
        target_type: type[Any],
        param_name: str | None = None,
        description: str = "",
    ) -> None:
        """Register a dependency provider.

        AND semantics:
        - If only target_type is specified: matches any parameter with that type (any param name)
        - If both param_name and target_type are specified: parameter must have BOTH that param name AND type

        Note: target_type is MANDATORY - this is a typed functions framework.

        Args:
            provider: Callable that takes context and returns the dependency value
            target_type: Type annotation that will trigger this dependency (REQUIRED)
            param_name: Optional parameter name for stricter matching (param name + type)
            description: Human-readable description of the dependency

        Raises:
            ConfigurationError: If a provider with the same matching condition is already registered

        Examples:
            # Type-only matching (flexible parameter naming)
            registry.register(lambda ctx: Redis(...), target_type=Redis)

            # Param name + type matching (strict)
            registry.register(lambda ctx: 42, target_type=int, param_name="max_retries")
        """
        dep = DependencyProvider(provider, target_type, param_name, description)

        # Check for duplicate registration
        for existing in self._providers:
            if self._has_same_matching_condition(existing, dep):
                type_name = getattr(target_type, "__name__", str(target_type))
                if param_name:
                    raise ConfigurationError(
                        f"Dependency already registered with param_name={param_name!r} and target_type={type_name}. "
                        f"Each dependency must have a unique matching condition."
                    )
                else:
                    raise ConfigurationError(
                        f"Dependency already registered with target_type={type_name}. "
                        f"Each dependency must have a unique matching condition."
                    )

        self._providers.append(dep)

    def is_dependency(self, param_name: str, param: inspect.Parameter) -> bool:
        """Check if a parameter is a registered dependency.

        Args:
            param_name: Name of the parameter to check
            param: Parameter object with type annotation

        Returns:
            True if any provider matches this parameter
        """
        return any(provider.matches(param_name, param) for provider in self._providers)

    def get_dependency_param_names(self, sig: inspect.Signature) -> frozenset[str]:
        """Get names of all parameters in a signature that are dependencies.

        Args:
            sig: Function signature to check

        Returns:
            Frozen set of parameter names that match registered dependencies
        """
        return frozenset(name for name, param in sig.parameters.items() if self.is_dependency(name, param))

    def resolve(
        self,
        sig: inspect.Signature,
        context: DependencyContext,
    ) -> DependencyContext:
        """Resolve dependencies for a function signature.

        Only resolves dependencies that are explicitly declared in the
        function's signature and match registered providers.

        Important: All providers are resolved against the provided context
        simultaneously. Dependencies between providers are NOT supported.
        If a provider needs another dependency, it must be in the initial context.

        Args:
            sig: Function signature to resolve dependencies for
            context: Context dictionary containing available values (typically
                    client, secrets, function_call_info)

        Returns:
            Dictionary mapping parameter names to resolved dependency values
        """
        resolved: dict[str, Any] = {}

        for param_name, param in sig.parameters.items():
            # Find first matching provider
            for provider in self._providers:
                if provider.matches(param_name, param):
                    resolved[param_name] = provider.resolve(context)
                    break  # Use first match only

        return resolved

    def resolve_for_function(
        self,
        func: Callable[..., Any],
        context: DependencyContext,
    ) -> DependencyContext:
        """Resolve dependencies for a function.

        Convenience method that extracts the signature and resolves dependencies.

        Args:
            func: Function to resolve dependencies for
            context: Context dictionary containing available values

        Returns:
            Dictionary mapping parameter names to resolved dependency values
        """
        sig = inspect.signature(func)
        return self.resolve(sig, context)

    def update(self, other: "DependencyRegistry") -> None:
        """Merge another registry into this one.

        Providers from the other registry are appended to this registry's provider list.

        Args:
            other: Registry to merge into this one
        """
        self._providers.extend(other._providers)

    @property
    def registered_dependencies(self) -> Sequence[DependencyInfo]:
        """Get information about all registered dependencies.

        Returns:
            Sequence of DependencyInfo tuples containing (target_type, param_name, description)
            for all registered providers. param_name is None for type-only providers.
        """
        return [DependencyInfo(p.target_type, p.param_name, p.description) for p in self._providers]


def create_default_registry() -> DependencyRegistry:
    """Create a registry with framework-provided dependencies.

    Framework dependencies use AND semantics for predictable behavior:
    - client: Must use name="client" AND type=CogniteClient (strict)
    - secrets: Must use name="secrets", AND a dict type (dict, Mapping, SecretsMapping, etc.)
    - logger: Must use name="logger" AND type=logging.Logger (strict)
    - function_call_info: Must use name="function_call_info" AND type=FunctionCallInfo (strict)

    User-provided dependencies should typically use target_type only, allowing
    flexible parameter naming (e.g., db, database, conn all work for Database type).

    Returns:
        DependencyRegistry with default framework dependencies
    """
    registry = DependencyRegistry()

    # CogniteClient - strict matching: param_name AND type required
    # This matches current Cognite Functions behavior where "client" is the standard parameter
    registry.register(
        provider=lambda ctx: ctx.get("client"),
        target_type=CogniteClient,
        param_name="client",
        description="CogniteClient instance - requires param_name='client' and type=CogniteClient",
    )

    # Secrets - param_name AND type matching: parameter must be named "secrets" with Mapping-compatible type
    # Supports dict, dict[str, str], Mapping, Mapping[str, str], etc.
    registry.register(
        provider=lambda ctx: ctx.get("secrets") or {},
        target_type=dict,
        param_name="secrets",
        description="Secrets mapping - requires param_name='secrets' and Mapping-compatible type",
    )

    # Logger - strict matching: param_name AND type required
    registry.register(
        provider=lambda ctx: get_function_logger(),
        target_type=logging.Logger,
        param_name="logger",
        description="Logger instance - requires param_name='logger' and type=logging.Logger",
    )

    # Function call info - strict matching: param_name AND type required
    registry.register(
        provider=lambda ctx: ctx.get("function_call_info"),
        target_type=FunctionCallInfo,
        param_name="function_call_info",
        description="Function call metadata - requires param_name='function_call_info' and type=FunctionCallInfo",
    )

    return registry


def resolve_dependencies(
    func: Callable[..., Any],
    client: CogniteClient,
    secrets: SecretsMapping | None = None,
    function_call_info: FunctionCallInfo | None = None,
    registry: DependencyRegistry | None = None,
    signature: inspect.Signature | None = None,
) -> DependencyContext:
    """Resolve dependencies for a function using standard framework parameters.

    This is a convenience function that combines context creation and dependency
    resolution in one call, reducing boilerplate in the framework.

    Args:
        func: Function to resolve dependencies for
        client: CogniteClient instance
        secrets: Optional secrets mapping
        function_call_info: Optional function call metadata
        registry: Optional custom registry (creates default if not provided)
        signature: Optional pre-computed signature (avoids re-inspection)

    Returns:
        Dictionary mapping parameter names to resolved dependency values
    """
    if registry is None:
        registry = create_default_registry()

    context = {
        "client": client,
        "secrets": secrets,
        "function_call_info": function_call_info,
    }

    # Use pre-computed signature if available, otherwise inspect the function
    if signature is not None:
        return registry.resolve(signature, context)
    return registry.resolve_for_function(func, context)
