"""Utility functions and classes for type checking and type hinting."""

from abc import ABC, abstractmethod
from collections.abc import Callable, MutableMapping
from typing import TYPE_CHECKING, Any, TypeGuard


def TypeHint[T](hint: type[T]) -> type[T]:  # noqa: N802
    """Add type hints from a specified class to a base class:

    >>> class Foo(TypeHint(Bar)):
    ...     pass

    This would add type hints from class ``Bar`` to class ``Foo``.
    """
    if TYPE_CHECKING:
        return hint  # This adds type hints for type checkers

    class _TypeHintBase: ...

    return _TypeHintBase


class ArrayLike(ABC):
    """A protocol representing array-like structures (list, tuple, set)."""

    @abstractmethod
    def __iter__(self) -> Any: ...

    @classmethod
    @abstractmethod
    def __subclasshook__(cls, subclass: type) -> bool:
        return hasattr(subclass, "__iter__") and subclass in (list, tuple, set)


class JSONLike(ABC):
    """A protocol representing JSON-like structures (dict, list)."""

    @abstractmethod
    def __setitem__(self, key: Any, value: Any) -> None: ...

    @abstractmethod
    def get(self, key: Any, default: Any = None) -> Any:
        """Get a value by key with an optional default."""

    @classmethod
    @abstractmethod
    def __subclasshook__(cls, subclass: type) -> bool:
        return hasattr(subclass, "__setitem__") and subclass in (dict, list)


def is_json_like(instance: Any) -> TypeGuard[JSONLike]:
    """Check if an instance is JSON-like (dict or list)."""
    return isinstance(instance, (dict | list))


def is_array_like(instance: Any) -> TypeGuard[ArrayLike]:
    """Check if an instance is array-like (list, tuple, set)."""
    return isinstance(instance, (list | tuple | set))


def is_mapping(doc: Any) -> TypeGuard[MutableMapping]:
    """Check if a document is a mutable mapping (like a dict)."""
    return isinstance(doc, MutableMapping) or (hasattr(doc, "__getitem__") and hasattr(doc, "__setitem__"))


def is_object(doc: Any) -> TypeGuard[object]:
    """Check if a document is a non-mapping object."""
    return (
        isinstance(doc, object)
        and not isinstance(doc, MutableMapping)
        and not isinstance(doc, (int | float | str | bool | list | tuple | set))
    )


def a_or_b(a: Callable, b: Callable) -> Callable[..., None]:
    """Return a function that applies either a or b based on the type of the document."""

    def wrapper(doc: Any) -> None:
        if is_mapping(doc):
            a(doc)
        elif is_object(doc):
            b(doc)

    return wrapper


__all__ = [
    "ArrayLike",
    "JSONLike",
    "TypeHint",
    "a_or_b",
    "is_array_like",
    "is_json_like",
    "is_mapping",
    "is_object",
]
