"""A Simple Stack implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Generator


class SimpleStack[T]:
    """A simple stack implementation."""

    def __init__(self, data: T | None = None) -> None:
        """Initialize an empty stack."""
        self._stack: list[T] = []
        if data is not None:
            self.push(data)

    def has(self, item: T) -> bool:
        """Check if the stack contains the given item."""
        return item in self.stack

    def push(self, item: T) -> None:
        """Push an item onto the stack."""
        self.stack.append(item)

    def extend(self, items: list[T]) -> None:
        """Extend the stack with a list of items."""
        self.stack.extend(items)

    def pop(self) -> T:
        """Pop an item off the stack. Raises IndexError if the stack is empty."""
        if self.is_empty:
            raise IndexError("pop from empty stack")
        value: T = self.stack.pop()
        if value is None:
            raise IndexError("pop from empty stack")
        return value

    def get(self, index: int) -> T:
        """Get an item from the stack by index."""
        return self.stack[index]

    def remove(self, item: T) -> None:
        """Remove the first occurrence of a value from the stack."""
        self.stack.remove(item)

    @property
    def is_empty(self) -> bool:
        """Check if the stack is empty."""
        return len(self.stack) == 0

    @property
    def not_empty(self) -> bool:
        """Check if the stack is not empty."""
        return not self.is_empty

    @property
    def size(self) -> int:
        """Get the current size of the stack."""
        return len(self.stack)

    @property
    def stack(self) -> list[T]:
        """Get the current stack."""
        return self._stack

    @stack.setter
    def stack(self, value: list[T]) -> None:
        """Set the current stack."""
        self._stack = value

    def clear(self) -> None:
        """Clear all items from the stack."""
        self._stack.clear()

    def copy(self) -> list[T]:
        """Get a copy of the current stack."""
        return self._stack.copy()

    def join(self, d: str = ", ") -> str:
        """Join the stack items into a single string with the given delimiter.

        Args:
            d (str): The delimiter to use between items. Defaults to ", ".

        Returns:
            str: The joined string of stack items.
        """
        return d.join(map(str, self.copy())) or ""

    def __contains__(self, item: T) -> bool:
        """Check if an item is in the stack."""
        return item in self.stack

    def __bool__(self) -> bool:
        """Check if the stack is not empty."""
        return self.not_empty

    def __getitem__(self, index: int) -> T:
        """Get an item from the stack by index."""
        return self.stack[index]

    def __setitem__(self, index: int, value: T) -> None:
        """Set an item in the stack by index."""
        self.stack[index] = value

    def __slice__(self, start: int | None = None, end: int | None = None, step: int | None = None) -> list[T]:
        """Get a slice of the stack."""
        return self.stack[slice(start, end, step)]

    def __len__(self) -> int:
        """Get the current size of the stack."""
        return self.size

    def __iter__(self) -> Generator[T, Any]:
        """Iterate over the stack from bottom to top."""
        yield from self.stack
