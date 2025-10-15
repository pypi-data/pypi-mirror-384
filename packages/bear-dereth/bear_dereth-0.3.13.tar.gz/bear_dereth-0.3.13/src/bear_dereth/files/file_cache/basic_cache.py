"""A simple cache for JSONL data."""

from __future__ import annotations

from typing import TYPE_CHECKING, NoReturn

from bear_dereth.files.file_cache.base_cache import CacheBase

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable, Iterator


class BasicCache[T](CacheBase[list[T]]):
    """A basic cache."""

    def __init__(self, data: T | list[T] | None = None) -> None:
        """Initialize the cache.

        Args:
            data (T | list[T]): Initial data to add to the cache.
        """
        super().__init__()
        self.add(data) if data is not None else None

    def invalidate(self) -> None:
        """Invalidate the cache."""
        self.clear()

    def clear(self) -> None:
        """Clear the cache."""
        self._root.clear()

    def add(self, item: T | list[T]) -> None:
        """Append an item to the cache.

        Args:
            item (T | list[T]): Item or list of items to add to the cache.
        """
        if isinstance(item, (str | dict)):
            self._root.append(item)
        elif isinstance(item, list):
            for sub_item in item:
                self.add(sub_item)

    def extend(self, items: Iterable[T]) -> None:  # type: ignore[override]
        """Extend the cache with multiple items.

        Args:
            items (Iterable[T]): An iterable of items to add to the cache.
        """
        for item in items:
            self.add(item)

    def __next__(self) -> Generator[T, NoReturn]:
        yield from self._root

    def __iter__(self) -> Iterator[T]:  # type: ignore[override]
        return super().__iter__()  # type: ignore[return-value]
