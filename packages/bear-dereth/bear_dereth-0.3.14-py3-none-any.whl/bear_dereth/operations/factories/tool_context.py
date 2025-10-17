"""Context for tools that operate on documents and collections."""

from __future__ import annotations

from abc import ABC, abstractmethod
from threading import RLock
from typing import TYPE_CHECKING, Any, overload

from bear_dereth.di import Singleton
from bear_dereth.lazy_imports import lazy
from bear_dereth.operations.common import CollectionChoice, default_factory

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType

copy: ModuleType = lazy("copy")
_lock = RLock()


class InjectionBase(ABC):
    """Base class for tools that can be injected into operations."""

    @abstractmethod
    def clone(self) -> Any:
        """Return a shallow clone of the tool."""


class ToolContext[T](InjectionBase):
    """Mutable context that exposes field helpers and collection factories."""

    _singleton: Singleton[ToolContext[T]] | None = None

    def __init__(self, doc: T | None = None, *, choice: CollectionChoice = "dict") -> None:
        """Context for a tool that allows for operations on mappings and objects."""
        self._doc: T | None = doc
        self._choice: CollectionChoice = choice
        self._factory_override: Callable[..., Any] | None = None
        self._retval = None

    @property
    def doc(self) -> T:
        """The currently bound document."""
        if self._doc is None:
            raise ValueError("ToolContext has no bound document")
        return self._doc

    @doc.setter
    def doc(self, value: T) -> None:
        self._doc = value

    def update(self, doc: T | None = None, *, choice: CollectionChoice | None = None) -> None:
        """Update the currently bound document and optionally override the default choice."""
        if doc is not None:
            self.doc = doc
        if choice is not None:
            self._choice = choice

    def set_default_choice(self, choice: CollectionChoice) -> None:
        """Set the default collection choice used when auto-injecting factories."""
        self._choice = choice

    def clone(self) -> ToolContext[T]:
        """Shallow clone the context for temporary overrides.

        ``copy`` is shallow so we maintain the same doc reference by design.
        """
        clone: ToolContext[T] = copy.copy(self)
        return clone

    def with_factory(self, factory: Callable[..., Any]) -> ToolContext[T]:
        """Return a cloned context that uses the provided factory."""
        clone: ToolContext[T] = self.clone()
        clone._factory_override = factory
        return clone

    def clear_factory(self) -> None:
        """Clear any explicit factory override."""
        self._factory_override = None

    def factory(self, *, choice: CollectionChoice | None = None) -> Callable[..., Any]:
        """Return the active factory callable."""
        if self._factory_override is not None:
            return self._factory_override
        return default_factory(choice=choice or self._choice)

    def getter[V](self, field: str) -> V:  # type: ignore[override]
        """Retrieve a field from the bound document."""
        from bear_dereth.typing_tools import is_mapping

        if is_mapping(self.doc):
            return self.doc[field]
        return getattr(self.doc, field)

    if TYPE_CHECKING:
        from bear_dereth.typing_tools import LitFalse, LitTrue

        @overload
        def setter[V](self, f: str, v: V, return_val: LitTrue) -> V: ...

        @overload
        def setter[V](self, f: str, v: V, return_val: LitFalse = False) -> None: ...  # type: ignore[override]

    def setter[V](self, f: str, v: V, return_val: bool = False) -> V | None:  # type: ignore[override]
        """Set a field on the bound document."""
        from bear_dereth.typing_tools import is_mapping

        if is_mapping(self.doc):
            self.doc[f] = v
            if return_val:
                self._retval = v
        else:
            setattr(self.doc, f, v)
            if return_val:
                self._retval = v
        return self._return_value()

    def deleter(self, field: str) -> None:
        """Delete a field from the bound document."""
        from bear_dereth.typing_tools import is_mapping

        if is_mapping(self.doc):
            del self.doc[field]  # type: ignore[index]
            return
        delattr(self.doc, field)

    def _return_value(self) -> Any:
        retval: Any = self._retval
        self._retval = None
        return retval

    @classmethod
    def get_singleton(cls) -> ToolContext[Any]:
        """Return a shared ToolContext instance."""
        with _lock:
            if cls._singleton is None:
                cls._singleton = Singleton(cls)
            return cls._singleton.get()


FuncContext = ToolContext

# ruff: noqa: PLC0415

__all__ = ["FuncContext", "ToolContext"]
