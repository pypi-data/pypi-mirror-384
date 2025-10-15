"""Base classes for a simple cache system."""

from __future__ import annotations

from abc import ABC, ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, NoReturn, Protocol, get_origin

from singleton_base._common import attr_name as attrib_name

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable, Iterator


class Container(Protocol):
    """Protocol for a container that supports basic operations."""

    def clear(self) -> None:
        """Clear the container."""

    def __len__(self) -> int: ...
    def __iter__(self) -> Iterator: ...


@dataclass(slots=True, frozen=True)
class PerClassData[T: Container]:
    """Holds per-class data for the cache metaclass."""

    root_object: type[T]

    def get(self) -> T:
        """Return the root object."""
        origin: Any = get_origin(self.root_object)
        if not isinstance(origin, type) or origin is None:
            raise TypeError(f"root_type {origin} is not a class and cannot be instantiated")
        return origin()


class CacheMeta[T: Container](ABCMeta):
    """Metaclass to handle generic type parameters for CacheBase."""

    @property
    def attr_name(cls) -> str:
        """Return the attribute name for the PerClassData instance."""
        return attrib_name(cls.__name__)

    @property
    def cls_data(cls) -> PerClassData[T]:
        """Return the PerClassData instance for the class."""
        try:
            return getattr(cls, cls.attr_name)
        except AttributeError as exc:
            raise RuntimeError(f"Cache class {cls.__name__} not properly initialized") from exc

    def __new__(mcs, name: str, bases: tuple, namespace: dict, **kwargs):
        """Create a new class, adding PerClassData if the class is generic."""
        if not bases or name == "CacheBase":
            return super().__new__(mcs, name, bases, namespace, **kwargs)
        if "__orig_bases__" in namespace:
            for base in namespace["__orig_bases__"]:
                if hasattr(base, "__args__"):  # type: ignore[attr-defined]
                    root_type: type[T] = base.__args__[0]  # type: ignore[attr-defined]
                    attr_name: str = attrib_name(name)
                    namespace[attr_name] = PerClassData[T](root_object=root_type)
                    break
        return super().__new__(mcs, name, bases, namespace, **kwargs)


class CacheBase[Root_T: Container](ABC, metaclass=CacheMeta):
    """Base class for a simple cache."""

    @classmethod
    def root_object(cls) -> Root_T:
        """Return the root object for the cache."""
        return cls.cls_data.get()

    def __init__(self) -> None:
        """Initialize the cache."""
        self._root: Root_T = self.root_object()

    @abstractmethod
    def invalidate(self) -> None:
        """Invalidate the cache."""

    def clear(self) -> None:
        """Clear the cache."""
        if hasattr(self._root, "clear") and callable(self._root.clear):
            self._root.clear()

    @abstractmethod
    def add(self, item: Any) -> None:
        """Add an item to the cache."""

    @abstractmethod
    def extend(self, items: Iterable[Any]) -> None:
        """Extend the cache with multiple items."""

    def empty(self) -> bool:
        """Check if the cache is empty."""
        return len(self._root) == 0

    def __bool__(self) -> bool:
        """Check if the cache has any items."""
        return not self.empty()

    def __next__(self) -> Generator[Any, NoReturn]:
        """Return the next item from the cache."""
        yield from self._root

    def __iter__(self) -> Iterator[Any]:
        """Return an iterator over the cached items."""
        return iter(self._root)

    def __len__(self) -> int:
        """Return the number of items in the cache."""
        return len(self._root)
