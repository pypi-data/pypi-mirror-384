"""Dependency injection markers and protocols."""

from __future__ import annotations

from dataclasses import dataclass
from functools import wraps
from types import NoneType
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    ParamSpec,
    Protocol,
    Self,
    TypeGuard,
    TypeVar,
    runtime_checkable,
)

from bear_dereth.di._resources import Resource, Singleton
from bear_dereth.exceptions import CannotFindTypeError, CannotInstantiateObjectError

if TYPE_CHECKING:
    from collections.abc import Callable
    from inspect import BoundArguments, Parameter, Signature

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


def _provide_check(name: str, param: Parameter, kwargs: frozenset) -> bool:
    """Check if a parameter is of type Provide."""
    from bear_dereth.introspection.general import isinstance_in_annotation, not_in_bound

    return isinstance_in_annotation(param, Provide, "default") and not_in_bound(kwargs, name)


def _get_provide_params(s: Signature, kwargs: frozenset) -> dict[str, Parameter]:
    """Get the parameters that are of type Provide."""
    return {n: p for n, p in s.parameters.items() if (_provide_check(n, p, kwargs))}


class Parser:
    """Parser for function parameters."""

    def __init__(
        self,
        param: Parameter,
        func: Callable,
    ) -> None:
        """Initialize the parser."""
        self.name: str = param.name
        self.func: Callable[..., Any] = func
        self.param: Parameter = param

    @property
    def container(self) -> type[DeclarativeContainer]:
        """Get the container from the parameter default."""
        return self.param.default.container

    @property
    def is_present(self) -> bool:
        """Check if the service is present in the container."""
        return self.container.has(self.name)

    @property
    def annotation(self) -> type | str:
        return self.param.annotation

    def is_singleton(self, service_type: type | None | str) -> TypeGuard[Singleton]:
        """Check if the service is a singleton."""
        return isinstance(service_type, Singleton)

    def is_resource(self, service_type: type | None | str) -> TypeGuard[Resource]:
        """Check if the service is a resource."""
        return isinstance(service_type, Resource)

    def _parsing(self) -> Result:
        """Alternative implementation showing annotation-first approach."""
        from bear_dereth.operations.funcstuffs import get_instance

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
            service_instance: None | type = get_instance(cached_instance)
            if service_instance is not None:
                return Result(instance=service_instance, success=True)
        # Step 3: Create new instance from resolved type
        if service_instance := get_instance(resolved_type):
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
        from bear_dereth.introspection import introspect_types

        resolved_type = introspect_types(self.param, self.func, default=NoneType)
        if resolved_type is not NoneType and isinstance(resolved_type, type):
            # TODO: Account for callables and other such insanity
            return resolved_type
        # Defined instances without being registered (console: Console = Console(...))
        instance: Any | None = self.container.get(self.name)
        if instance is not None:
            return type(instance)
        return None

    @classmethod
    def get(cls, param: Parameter, func: Callable) -> Result:
        """Work the parsing logic and return Metadata."""
        parser: Self = cls(param, func)
        try:
            return parser._parsing()
        except Exception as e:
            return Result(exception=e, success=False)


def parse_params(func: Callable, *args, **kwargs) -> tuple[tuple[Any, ...], dict[str, Any]]:
    """Parse the parameters of a function."""
    from bear_dereth.introspection import get_function_signature

    s: Signature = get_function_signature(func)
    b: BoundArguments = s.bind_partial(*args, **kwargs)
    provided_names: frozenset[str] = frozenset(b.arguments.keys())
    params: dict[str, Parameter] = _get_provide_params(s=s, kwargs=provided_names)
    for name, p in params.items():
        result: Result = Parser.get(param=p, func=func)
        if not result.success and result.exception is not None:
            p.default.result = result
        if result.success:
            container: DeclarativeContainer = p.default.container
            b.arguments[name] = result.instance
            container.override(name, result.instance)
    b.apply_defaults()
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


# ruff: noqa: PLC0415
