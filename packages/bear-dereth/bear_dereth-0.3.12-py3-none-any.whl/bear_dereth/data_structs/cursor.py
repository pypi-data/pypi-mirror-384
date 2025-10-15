"""A simple cursor to track position in a collection."""

from collections.abc import Iterator
from typing import Any, Protocol

from bear_dereth.math.general import clamp, neg


class CollectionProtocol(Protocol):
    """A protocol for collections that support len() and indexing."""

    def __len__(self) -> int: ...
    def __getitem__(self, index: int) -> Any: ...
    def __setitem__(self, index: int, value: Any) -> None: ...
    def pop(self) -> Any: ...  # noqa: D102
    def remove(self, item: Any) -> None: ...  # noqa: D102
    def get(self, index: int) -> Any: ...  # noqa: D102
    def copy(self) -> Any: ...  # noqa: D102
    def clear(self) -> None: ...  # noqa: D102
    def join(self, d: str) -> str: ...  # noqa: D102


class BaseCursor[Collection_T: CollectionProtocol, ReturnType: Any]:
    """A simple cursor to track position in a collection."""

    def __init__(
        self,
        collection: type[Collection_T],
        default: Any | None = None,
        *args,
        **kwargs,
    ) -> None:
        """A simple cursor to track position in a collection.

        Args:
            collection (type[Collection_T]): The collection type to use for the cursor.
            default (Any | None, optional): The default value to return if the collection is empty. Defaults to None.
            *args: Arguments to pass to the collection constructor if a type is provided.
            **kwargs: Keyword arguments to pass to the collection constructor if a type is provided.
        """
        self._factory: type[Collection_T] = collection
        self._collection: Collection_T | None = None
        self._args: tuple[Any, ...] = args
        self._kwargs: dict[str, Any] = kwargs
        self._default: Any = default
        self._index: int = 0

    @property
    def collection(self) -> Collection_T:
        """Get the current collection."""
        if self._collection is None:
            self._collection = self._factory(*self._args, **self._kwargs)
        return self._collection

    @property
    def index(self) -> int:
        """Get the current index of the cursor."""
        return self.clamped(self._index)

    @index.setter
    def index(self, value: int) -> None:  # noqa: ARG002
        raise ValueError("Index cannot be set directly, use move() instead.")

    def set_index(self, value: int) -> None:
        """Set the current index of the cursor."""
        self._index = self.clamped(value)

    def tick(self) -> None:
        """Move the cursor forward by one."""
        self._move(1)

    def tock(self) -> None:
        """Move the cursor backward by one."""
        self._move(neg(1))

    def head(self) -> None:
        """Move the cursor to the beginning of the collection."""
        self._move(head=True)

    def tail(self) -> None:
        """Move the cursor to the end of the collection."""
        self._move(tail=True)

    def _update(self, collection: Collection_T) -> None:
        """Update the collection and clamp the index to the new bounds."""
        self._collection = collection

    def _move(self, offset: int | None = None, tail: bool = False, head: bool = False) -> None:
        """Move the cursor by the given offset."""
        if head and tail:
            raise ValueError("Cannot move to both head and tail.")
        if not head and not tail and offset is not None:
            self.set_index(self.index + offset)
        elif head:
            self.set_index(self.lower)
        elif tail:
            self.set_index(self.upper)

    def offset(self, v: int) -> None:
        """Move the cursor by the given offset."""
        self._move(offset=v)

    def get(self, offset: int | None = None) -> ReturnType:
        """Get an item in the collection at the given offset from the current index."""
        target_index: int = self.clamped(self.index + (offset if offset is not None else 0))
        return self.collection.get(target_index) if self.not_empty else self._default

    def peek(self, offset: int = 0, tail: bool = False, head: bool = False) -> ReturnType:
        """Peek at an item in the collection at the given offset from the current index."""
        if head and tail:
            raise ValueError("Cannot peek at both head and tail.")
        if head:
            target_index = self.lower
        elif tail:
            target_index = self.upper
        else:
            target_index: int = self.clamped(self.index + offset)
        return self.collection[target_index] if self.not_empty else self._default

    def reset(self) -> None:
        """Reset the cursor to the beginning of the collection."""
        self.head()

    def clear(self) -> None:
        """Clear all items from the collection."""
        self.collection.clear()
        self.reset()

    def clamped(self, v: int) -> int:
        """Clamp the given value to the bounds of the cursor."""
        return clamp(v, self.lower, self.upper)

    def copy(self) -> Collection_T:
        """Get a copy of the current collection."""
        return self.collection.copy()

    def push(self, item: ReturnType) -> None:
        """Add an item to the end of the collection."""
        if hasattr(self.collection, "append"):
            self.collection.append(item)  # type: ignore[arg-type]
        elif hasattr(self.collection, "add"):
            self.collection.add(item)  # type: ignore[arg-type]
        elif hasattr(self.collection, "insert"):
            self.collection.insert(self.size, item)  # type: ignore[arg-type]
        else:
            raise NotImplementedError("Collection type does not support adding items.")

    def pop(self, index: int | None = None) -> ReturnType:
        """Remove and return an item from the collection.

        Args:
            index (int | None, optional): The index of the item to remove. If None, removes the item at the current cursor position. Defaults to None.

        Returns:
            ReturnType: The removed item.
        """
        if self.is_empty:
            raise IndexError("pop from empty collection")
        target_index: int = self.clamped(self.index if index is None else index)
        item: ReturnType = self.collection[target_index]
        self.collection.remove(item)
        return item

    @property
    def current(self) -> ReturnType:
        """Get the current item in the collection."""
        return self.collection[self.index] if self.not_empty else self._default

    @property
    def lower(self) -> int:
        """Get the lower bound of the cursor."""
        return 0

    @property
    def upper(self) -> int:
        """Get the upper bound of the cursor."""
        return self.size - 1

    @property
    def size(self) -> int:
        """Get the size of the collection."""
        return len(self)

    @property
    def is_empty(self) -> bool:
        """Check if the collection is empty."""
        return self.size == 0

    @property
    def not_empty(self) -> bool:
        """Check if the collection is not empty."""
        return self.size > 0

    @property
    def within_bounds(self) -> bool:
        """Check if the current index is within the bounds of the collection."""
        return self.lower <= self.index <= self.upper

    def join(self, d: str = ", ") -> str:
        """Join the collection items into a single string with the given delimiter.

        Args:
            d (str): The delimiter to use between items. Defaults to ", ".

        Returns:
            str: The joined string of collection items.
        """
        return self.collection.join(d) if self.not_empty else ""

    def __len__(self) -> int:
        return len(self.collection)

    def __iter__(self) -> Iterator[ReturnType]:
        return iter(self.collection)
