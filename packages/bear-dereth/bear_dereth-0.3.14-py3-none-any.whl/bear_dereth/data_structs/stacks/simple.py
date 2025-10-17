"""A Simple Stack implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, LiteralString

from bear_dereth.math.general import neg
from bear_dereth.math.infinity import INFINITE

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


OverflowStrat = Literal["strict", "silent", "drop_oldest", "drop_newest"]
OverflowChoices: tuple[LiteralString, ...] = ("strict", "silent", "drop_oldest", "drop_newest")


class BoundedStack[T](SimpleStack[T]):
    """A stack with a maximum size."""

    def __init__(
        self,
        max_size: int = INFINITE,
        data: T | None = None,
        *,
        overflow: OverflowStrat = "silent",
        resize: bool = False,
    ) -> None:
        """Initialize a bounded stack with a maximum size."""
        super().__init__(data)
        self.max_size: int = max_size
        self.overflow: OverflowStrat = overflow if overflow in OverflowChoices else "silent"
        self.push_attr: LiteralString = f"_push_{self.overflow}"
        self.resize: bool = resize
        if self.size > self.max_size:
            self.stack = self.stack[-self.max_size :]

    def _push_strict(self, item: T) -> None:
        """Push an item onto the stack, raising an error if the stack is full."""
        if self.is_full:
            raise OverflowError("Stack overflow: maximum size reached")
        super().push(item)

    def _push_silent(self, item: T) -> None:
        """Push an item onto the stack, ignoring if the stack is full."""
        if not self.is_full:
            super().push(item)

    def _push_drop_newest(self, item: T) -> None:
        """Push an item onto the stack, removing the newest item if the stack is full."""
        if self.is_full:
            self.stack.pop()
        super().push(item)

    def _push_drop_oldest(self, item: T) -> None:
        """Push an item onto the stack, removing the oldest item if the stack is full."""
        if self.is_full:
            self.stack.pop(0)
        super().push(item)

    def push(self, item: T) -> None:
        """Push an item onto the stack. If the stack exceeds max_size, remove the oldest item."""
        getattr(self, self.push_attr)(item)

    def extend(self, items: list[T]) -> None:
        """Extend the stack with a list of items, respecting the maximum size."""
        for item in items:
            self.push(item)
        if self.resize and self.size > self.max_size:
            self.stack = self.stack[-self.max_size :]

    def resize_stack(
        self,
        new_size: int,
        *,
        strict: bool = False,
        keep_oldest: bool | None = None,
        keep_newest: bool | None = None,
    ) -> None:
        """Resize the stack to a new maximum size."""
        if new_size <= 0:
            raise ValueError("new_size must be greater than 0")
        if new_size == self.max_size:
            return
        self.max_size = new_size
        if self.size > self.max_size:
            if self.overflow == "strict" or strict:
                raise OverflowError("Stack overflow: maximum size reached after resize")
            if keep_oldest is not None or self.overflow == "drop_newest":
                self.stack = self.stack[: self.max_size]
            elif keep_newest is not None or self.overflow == "drop_oldest":
                self.stack = self.stack[neg(self.max_size) :]
            else:  # drop_oldest by default
                self.stack = self.stack[neg(self.max_size) :]

    @property
    def is_full(self) -> bool:
        """Check if the stack is full."""
        return self.size >= self.max_size

    @property
    def capacity(self) -> int:
        """Get the maximum size of the stack."""
        return self.max_size

    @property
    def space_left(self) -> int:
        """Get the remaining space in the stack."""
        return self.max_size - self.size
