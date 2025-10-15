"""Dependency injection markers and protocols."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from functools import wraps
from inspect import BoundArguments, Parameter, Signature, isclass
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    ParamSpec,
    Protocol,
    Self,
    TypeGuard,
    TypeVar,
    get_args,
    get_origin,
    runtime_checkable,
)

from bear_dereth.di._resources import Resource, Singleton
from bear_dereth.exceptions import CannotFindTypeError, CannotInstantiateObjectError
from bear_dereth.introspection import find_type_hints, get_function_signature

if TYPE_CHECKING:
    from collections.abc import Callable

    from bear_dereth.di import DeclarativeContainer


@dataclass(slots=True, frozen=True)
class Result:
    """Result for a service."""

    exception: Exception | None = None
    instance: Any | None = None
    success: bool = True

    @property
    def error(self) -> str:
        """Extract the exception as a string."""
        return str(self.exception) if self.exception is not None else ""


if TYPE_CHECKING:

    @runtime_checkable
    class Provider[T: DeclarativeContainer](Protocol):
        """Marker for a service to be injected."""

        _container: ClassVar[type[DeclarativeContainer] | DeclarativeContainer]

        service_name: str
        result: Result
        container: type[T] | T

        @classmethod
        def has_container(cls) -> bool: ...
        @classmethod
        def set_container(cls, container: type[T] | T) -> None: ...
        @classmethod
        def get_container(cls) -> type[T]: ...
        def __new__(cls, *args: Any, **kwargs: Any) -> Self: ...
        def __init__(self, service_name: str, container: type[T] | T) -> None: ...
        def __call__(self, *args, **kwargs) -> Self: ...
        def __getattr__(self, item: str) -> Self: ...
        def __getitem__(self, item: Any) -> Any: ...
        def __class_getitem__(cls, item: Any) -> Self: ...

    Provide: Provider  # HACK: This stuff is a a nightmare :)
else:

    class Provider[T: DeclarativeContainer]:
        """Marker for a service to be injected."""

        __IS_MARKER__: bool = True

        _container: ClassVar[type[T] | T | None] = None

        @classmethod
        def has_container(cls) -> bool:
            """Check if a container has been set."""
            return cls._container is not None

        @classmethod
        def set_container(cls, container: type[T] | type) -> None:
            """Set the container class for this provider."""
            cls._container = container

        @classmethod
        def get_container(cls) -> type[T] | T:
            """Get the container class for this provider."""
            if cls._container is None:
                raise ValueError("Container has not been set.")
            return cls._container

        def __init__(self, service_name: str, container: type[T] | T | None = None) -> None:
            """Marker for a service to be injected."""
            self.service_name: str = service_name
            self.container = container or self.get_container()

        @classmethod
        def __class_getitem__(cls, item: Any) -> Provide:
            """Return a Provide instance for the given item."""
            if isinstance(item, Provide) or hasattr(item, "service_name"):
                return item
            if isinstance(item, (Resource | Singleton)) and hasattr(item, "service_name") and item.service_name:
                return cls(item.service_name, cls.get_container())
            if hasattr(item, "__name__"):
                return cls(item.__name__.lower())
            if isinstance(item, str):
                return cls(item)
            return cls(str(item))  # Try to extract service name from the item

        def __repr__(self) -> str:
            return f"Provide(service_name={self.service_name}, container={self.container.__name__ or 'None'})"

    class Provide(Provider): ...


def _is_provide(name: str, param: Parameter, kwargs: frozenset) -> bool:
    """Check if a parameter is of type Provide."""
    return param.default != Parameter.empty and isinstance(param.default, Provider) and name not in kwargs


def _get_provide_params(s: Signature, kwargs: frozenset) -> dict[str, Parameter]:
    """Get the parameters that are of type Provide."""
    return {name: param for name, param in s.parameters.items() if (_is_provide(name, param, kwargs))}


class Parser:
    """Parser for function parameters."""

    def __init__(
        self,
        name: str,
        func: Callable,
        param: Parameter,
    ) -> None:
        """Initialize the parser."""
        self.name: str = name
        self.func: Callable[..., Any] = func
        self.param: Parameter = param
        # from rich import inspect

        # inspect(self)

    @property
    def container(self) -> type[DeclarativeContainer]:
        """Get the container from the parameter default."""
        return self.param.default.container

    @property
    def is_present(self) -> bool:
        """Check if the service is present in the container."""
        return self.container.has(self.name)

    @property
    def service_type(self) -> type | str:
        return self.param.annotation

    @staticmethod
    def get_service_instance(service: Any) -> None | type:
        """Get the service instance, instantiating if necessary."""
        try:
            if isclass(service):
                return service()
            return service
        except Exception:
            return None

    @staticmethod
    def _resolve_string_to_type(type_name: str, func: Callable) -> type | None:
        """Helper to resolve string type names to actual types."""
        with suppress(NameError, AttributeError, KeyError, TypeError):
            resolved_type: Any | None = find_type_hints(type_name, func)
            if resolved_type is not None:
                return resolved_type
            global_type: Any | None = func.__globals__.get(type_name)
            if global_type is not None and isinstance(global_type, type):
                return global_type
        return None

    @staticmethod
    def _resolve_annotated(name: str, func: Callable) -> type | None:
        """Resolve a service by name from the function's global scope."""
        origin: ParamSpec | None = get_origin(name)
        if origin is not None:
            args: tuple[Any, ...] = get_args(name)
            if args:
                first_arg = args[0]
                if isinstance(first_arg, type):
                    return first_arg
                if isinstance(first_arg, str):
                    return Parser._resolve_string_to_type(first_arg, func)
                if get_origin(first_arg) is not None:  # Handle nested generics like Union[Console, str]
                    return Parser._resolve_annotated(first_arg, func)
                return first_arg
        return None

    def is_singleton(self, service_type: type | None | str) -> TypeGuard[Singleton]:
        """Check if the service is a singleton."""
        return isinstance(service_type, Singleton)

    def is_resource(self, service_type: type | None | str) -> TypeGuard[Resource]:
        """Check if the service is a resource."""
        return isinstance(service_type, Resource)

    def _parsing(self) -> Result:
        """Alternative implementation showing annotation-first approach."""
        # Step 1: Resolve what type we need to create
        resolved_type: type | None = self._resolve_to_concrete_type()
        if resolved_type is None:
            return Result(
                exception=CannotFindTypeError(f"Could not resolve type for service '{self.name}'"),
                success=False,
            )
        # Step 2: Check if we have a cached instance (optimization)
        if self.is_present:
            cached_instance: Any | None = self.container.get(self.name)
            service_instance: None | type = self.get_service_instance(cached_instance)
            if service_instance is not None:
                return Result(instance=service_instance, success=True)
        # Step 3: Create new instance from resolved type
        if service_instance := self.get_service_instance(resolved_type):
            return Result(instance=service_instance, success=True)
        # Step 4: Everything failed
        return Result(exception=CannotInstantiateObjectError(f"Could not create service '{self.name}'"), success=False)

    def _resolve_to_concrete_type(self) -> type | None:
        """Parse any annotation type into a concrete, instantiable type.

        This is the heart of the contract resolution - it handles:
        - Direct types: Console -> Console
        - String annotations: "Console" -> Console class from globals
        - Complex types: Union[A, B], Annotated[A, "meta"] -> A

        Returns: Result with the concrete type to instantiate, or error
        """
        resolved_type = None
        # Case 1: Direct type annotation (console: Console)
        if isinstance(self.service_type, type):
            return self.service_type
        # Case 2: String annotation (console: "Console") Forward references
        if isinstance(self.service_type, str):
            resolved_type: Any | None = self._resolve_string_to_type(self.service_type, self.func)
            if isinstance(resolved_type, type):
                return resolved_type
        # Case 3: Complex generic types (Union, Annotated, Optional, etc.
        if get_origin(self.service_type) is not None:
            resolved_type: Any | None = self._resolve_annotated(self.service_type, self.func)
            if isinstance(resolved_type, type):
                return resolved_type
        # Case 4: Defined instances without being registered (console: Console = Console(...))
        instance = self.container.get(self.name)
        if instance is not None:
            return type(instance)
        return None

    @classmethod
    def get(cls, name: str, func: Callable, param: Parameter) -> Result:
        """Work the parsing logic and return Metadata."""
        parser: Self = cls(name, func, param)
        try:
            return parser._parsing()
        except Exception as e:
            return Result(exception=e, success=False)


def parse_params(func: Callable, *args, **kwargs) -> tuple[tuple[Any, ...], dict[str, Any]]:
    """Parse the parameters of a function."""
    s: Signature = get_function_signature(func)
    b: BoundArguments = s.bind_partial(*args, **kwargs)
    provided_names: frozenset[str] = frozenset(b.arguments.keys())
    params: dict[str, Parameter] = _get_provide_params(s=s, kwargs=provided_names)
    for name, p in params.items():
        result: Result = Parser.get(name, func, p)
        if not result.success and result.exception is not None:
            p.default.result = result
        if result.success:
            container: DeclarativeContainer = p.default.container
            b.arguments[name] = result.instance
            container.override(name, result.instance)
    return b.args, b.kwargs


P = ParamSpec("P")
T = TypeVar("T")


def inject(func: Callable[P, T]) -> Callable[P, T]:  # noqa: UP047
    """Decorator that auto-injects dependencies"""

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        bound_args, bound_kwargs = parse_params(func, *args, **kwargs)
        return func(*bound_args, **bound_kwargs)

    return wrapper
