"""Classes for various operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from bear_dereth.operations.iterstuffs import merge_lists

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from inspect import Signature


class Massaman:
    """Generalized currying that plays nice with functools.partial.

    Massaman is my favorite curry, thus the name.  It works by storing
    the function, args, and kwargs, and only calling the function
    when all required arguments are provided.
    """

    def __init__(self, func: Any, *args: Any, **kwargs: Any) -> None:
        """Initialize the Curry object."""
        from bear_dereth.introspection import get_function_signature  # noqa: PLC0415

        if hasattr(func, "func") and hasattr(func, "args"):
            base_func: Callable = func.func
            base_args: tuple = getattr(func, "args", ())
            base_kwargs: dict = getattr(func, "keywords", {}) or getattr(func, "kwargs", {})

            self.func: Callable = base_func
            self.args: tuple = base_args + args
            self.kwargs: dict = base_kwargs | kwargs
        else:
            self.func = func
            self.args = args
            self.kwargs = kwargs

        self.sig: Signature = get_function_signature(self.func)

    def __call__(self, *new_args: Any, **new_kwargs: Any) -> Any:
        """Call the curried function with additional arguments."""
        combined_args: tuple = self.args + new_args
        combined_kwargs: dict = self.kwargs | new_kwargs
        if self.is_fully_curried:
            return self.func(*combined_args, **combined_kwargs)
        return Massaman(self.func, *combined_args, **combined_kwargs)

    @property
    def is_fully_curried(self) -> bool:
        """Check if the function has been fully curried."""
        try:
            self.sig.bind(*self.args, **self.kwargs)
            return True
        except TypeError:
            return False

    def __repr__(self) -> str:
        return f"Curry({self.func.__name__}, args={self.args}, kwargs={self.kwargs})"


class ListMerge[T]:
    """Merge multiple lists into one, with options for string representation."""

    @classmethod
    def merge_items(cls, *args: list[T], unique: bool = False) -> list[T]:
        """Merge multiple lists into one.

        Args:
            *args (list[T]): Lists to combine.
            unique (bool): If True, only unique items will be kept. Defaults to False.

        Returns:
            list[T]: The merged list.
        """
        return merge_lists(*args, unique=unique)

    def __init__(self, *args: list[T], unique: bool = False) -> None:
        """Merge multiple lists into one.

        Args:
            *args (list[T]): Lists to combine.
            unique (bool): If True, only unique items will be kept. Defaults to False.
        """
        self._merged: list[T] = self.merge_items(*args, unique=unique) if args else []
        self.unique: bool = unique

    @property
    def merged(self) -> list[T]:
        """Return the merged list."""
        return self._merged

    def add(self, items: list[T]) -> Self:
        """Add a list of items to be merged later."""
        self._merged = self.merge_items(self._merged, items, unique=self.unique)
        return self

    def merge(self, *args: list[T], unique: bool | None = None) -> list[T]:
        """Combine additional lists into the existing merged list.

        Meant to be used last, after any delayed adds.

        Args:
            *args (list[T]): Lists to combine.
        """
        _unique: bool = self.unique if unique is None else unique
        self._merged = self.merge_items(self._merged, *args, unique=_unique)
        return self.merged

    def as_list(self) -> list[T]:
        """Return the merged list.

        Meant to be used last, after any delayed adds when you have nothing else to merge.
        """
        return self.merged

    def as_string(self, sep: str = "\n") -> str:
        """Return the merged list as a string, joined by the specified separator."""
        return sep.join(map(str, self.merged))

    def __repr__(self) -> str:
        return f"ListMerge(merged={self.merged}, unique={self.unique})"

    def __str__(self) -> str:
        return self.as_string()

    def __len__(self) -> int:
        return len(self.merged)

    def __iter__(self) -> Iterator[T]:
        return iter(self.merged)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None: ...
