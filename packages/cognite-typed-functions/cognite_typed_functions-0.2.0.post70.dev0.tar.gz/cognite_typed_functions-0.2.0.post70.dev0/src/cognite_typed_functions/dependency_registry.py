"""Dependency injection system for Cognite Functions.

This module provides a flexible dependency injection system that allows the framework
to inject dependencies like CogniteClient, secrets, and logger into route endpoints,
while also allowing users to register their own custom dependencies.

The DI system follows these principles:
- Dependencies are only injected if explicitly declared in function signatures
- Type-safe: dependencies are resolved based on parameter name AND type
- Extensible: users can register custom dependency providers
- Framework-provided dependencies are registered by default

Matching Semantics (AND logic):
- ALL dependencies require BOTH param_name AND target_type (strict AND semantics)
- This ensures predictable behavior and consistent naming across endpoints
- Each dependency has a fixed parameter name (e.g., always "logger", never "log" or "my_logger")
- Type annotations are mandatory (this is a typed functions framework)

Current Limitations:
- Dependency chains between custom providers are NOT supported. All providers are
  resolved against the same initial context (client, secrets, function_call_info).
  A resolved dependency is not made available to other providers within the same
  resolution cycle.

  Example that will NOT work:
      registry.register(provider=lambda ctx: create_db(ctx["secrets"]),
                       target_type=Database, param_name="db")
      registry.register(provider=lambda ctx: UserRepo(db=ctx["db"]),  # KeyError!
                       target_type=UserRepository, param_name="repo")

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
        param_name: Required parameter name (dependencies must match both name and type)
        description: Human-readable description of the dependency
    """

    target_type: type[Any]
    param_name: str
    description: str


@dataclass(frozen=True)
class DependencyProvider:
    """Wrapper for a single dependency provider function.

    Encapsulates a provider function along with matching criteria (param_name and type).
    The provider function is invoked via the resolve() method.

    Matching behavior (AND semantics):
    - Dependencies MUST specify both param_name AND target_type
    - A parameter matches only if BOTH the name AND type match (strict AND logic)
    - This ensures predictable, consistent behavior across all endpoints

    Note: Both param_name and target_type are MANDATORY - this is a typed functions framework
    with strict naming conventions.
    """

    provider: ProviderFunction
    target_type: Any
    param_name: str
    description: str = ""

    def matches(self, param_name: str, param: inspect.Parameter) -> bool:
        """Check if this provider matches the given parameter.

        AND semantics:
        - Both param_name AND target_type must match
        - The parameter name must exactly match self.param_name
        - The parameter type must be compatible with self.target_type

        Args:
            param_name: Name of the parameter to check
            param: Parameter object with type annotation

        Returns:
            True if both name and type match
        """
        # Check name match first (fail fast)
        if self.param_name != param_name:
            return False

        # Check type match
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

    The registry maintains a collection of dependency providers that match parameters
    by BOTH name AND type using strict AND semantics. When resolving dependencies
    for a function, it only injects dependencies that are explicitly declared in the
    function's signature.

    Matching Logic (strict AND semantics):
    - Both param_name AND target_type are REQUIRED for all dependencies
    - A parameter matches only if BOTH the name AND type match
    - This ensures predictable, consistent naming across all endpoints

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
        param_name: str,
        description: str = "",
    ) -> None:
        """Register a dependency provider.

        Strict AND semantics:
        - Both param_name AND target_type are REQUIRED
        - A parameter matches only if BOTH the name AND type match
        - This ensures predictable, consistent behavior across all endpoints

        Args:
            provider: Callable that takes context and returns the dependency value
            target_type: Type annotation that will trigger this dependency (REQUIRED)
            param_name: Parameter name that will trigger this dependency (REQUIRED)
            description: Human-readable description of the dependency

        Raises:
            ConfigurationError: If a provider with the same matching condition is already registered

        Examples:
            # Framework dependencies (built-in)
            registry.register(lambda ctx: ctx["client"], target_type=CogniteClient, param_name="client")

            # Custom dependencies (user-defined)
            registry.register(lambda ctx: Redis(...), target_type=Redis, param_name="redis")
            registry.register(lambda ctx: 42, target_type=int, param_name="max_retries")
        """
        dep = DependencyProvider(provider, target_type, param_name, description)

        # Check for duplicate registration
        for existing in self._providers:
            if self._has_same_matching_condition(existing, dep):
                type_name = getattr(target_type, "__name__", str(target_type))
                raise ConfigurationError(
                    f"Dependency already registered with param_name={param_name!r} and target_type={type_name}. "
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
            for all registered providers.
        """
        return [DependencyInfo(p.target_type, p.param_name, p.description) for p in self._providers]


def create_default_registry() -> DependencyRegistry:
    """Create a registry with framework-provided dependencies.

    All framework dependencies use strict AND semantics (name + type):
    - client: Must use name="client" AND type=CogniteClient
    - secrets: Must use name="secrets" AND a dict-compatible type (dict, Mapping, etc.)
    - logger: Must use name="logger" AND type=logging.Logger
    - function_call_info: Must use name="function_call_info" AND type=FunctionCallInfo

    User-provided dependencies follow the same pattern and must specify both
    param_name and target_type for predictable, consistent behavior.

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
