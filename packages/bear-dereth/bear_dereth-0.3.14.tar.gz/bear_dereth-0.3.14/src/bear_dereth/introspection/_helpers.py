from __future__ import annotations

from dataclasses import dataclass
from inspect import Parameter
from types import GenericAlias
from typing import TYPE_CHECKING, Any, TypeGuard, get_args, get_origin

if TYPE_CHECKING:
    from inspect import _ParameterKind  # type: ignore[import]


def is_typed(p: str | type) -> TypeGuard[type]:
    """Check if a parameter has a non-Any type annotation."""
    return isinstance(p, type) and p is not Any


def is_str(p: str | type) -> TypeGuard[str]:
    """Check if a parameter's annotation is a string."""
    return isinstance(p, str)


def is_generic_alias(p: Any) -> TypeGuard[GenericAlias]:
    """Check if a parameter's annotation is a GenericAlias."""
    return isinstance(p, GenericAlias)


def is_annotated(p: Any) -> bool:
    """Check if a parameter's annotation is not an Annotated type."""
    return str(type(p)).endswith("<class 'typing._AnnotatedAlias'>")


def is_union(p: Any) -> bool:
    """Check if a parameter's annotation is a Union type."""
    return str(type(p)).endswith("<class 'typing._UnionGenericAlias'>")


def is_generic_callable(p: Any) -> bool:
    """Check if a parameter's annotation is a Generic Callable type."""
    return str(type(p)).endswith("<class 'collections.abc._CallableGenericAlias'>")


def is_not_generic(p: Any) -> bool:
    """Check if a parameter's annotation is not a Generic type."""
    return not is_union(p) and not is_annotated(p) and not is_generic_alias(p)


@dataclass(slots=True)
class ParamWrapper:
    """A wrapper around a Parameter to provide type introspection utilities."""

    param: Parameter

    @property
    def annotation(self) -> Any:
        return self.param.annotation

    @property
    def name(self) -> str:
        return self.param.name

    @property
    def kind(self) -> _ParameterKind:
        return self.param.kind

    @property
    def is_typed(self) -> bool:
        return is_typed(self.annotation)

    @property
    def is_str(self) -> bool:
        return is_str(self.annotation)

    @property
    def is_union(self) -> bool:
        return is_union(self.annotation)

    @property
    def is_annotated(self) -> bool:
        return is_annotated(self.annotation)

    @property
    def is_generic(self) -> bool:
        return is_generic_alias(self.annotation)

    @property
    def is_generic_callable(self) -> bool:
        return is_generic_callable(self.annotation)

    @property
    def is_concrete(self) -> bool:
        return not self.is_generic

    @property
    def origin(self) -> Any | None:
        return get_origin(self.annotation)

    @property
    def args(self) -> tuple[Any, ...]:
        return get_args(self.annotation)

    def from_annotation(self, annotation: Any) -> None:
        self.param = Parameter(name=self.param.name, kind=self.param.kind, annotation=annotation)

    def first_arg(self) -> Any | None:
        if args := self.args:
            return args[0]
        return None

    def unwrap_first(self) -> ParamWrapper:
        first: Any | None = self.first_arg()
        if first is not None:
            return ParamWrapper(Parameter(name=self.param.name, kind=self.param.kind, annotation=first))
        raise ValueError("No type arguments to unwrap.")
