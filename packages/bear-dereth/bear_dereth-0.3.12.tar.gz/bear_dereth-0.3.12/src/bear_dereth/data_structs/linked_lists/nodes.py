"""A node in a linked list."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass(slots=True)
class Node[T]:
    """A node in a linked list."""

    value: T
    prev: Node[T] | None = None
    next: Node[T] | None = None

    def __setattr__(self, name: str, value: Any) -> None:
        """Prevent changing the value of a null node."""
        if name == "value" and getattr(self, "value", None) == "__NULL__":
            raise AttributeError("Cannot change the value of a null node.")
        object.__setattr__(self, name, value)

    @property
    def is_linked(self) -> bool:
        """Check if the node is linked to any other node."""
        return self.prev is not None or self.next is not None

    @property
    def is_unlinked(self) -> bool:
        """Check if the node is unlinked from any other node."""
        return not self.is_linked

    @property
    def is_null(self) -> bool:
        """Check if the node is a null node."""
        return self.value == "__NULL__"

    @property
    def is_not_null(self) -> bool:
        """Check if the node is not a null node."""
        return not self.is_null

    def __iter__(self) -> Iterator[Node[T]]:
        """Iterate over next.next nodes."""
        node: Node[T] | None = self.next
        while node is not None:
            yield node
            node = node.next

    def __reversed__(self) -> Iterator[Node[T]]:
        """Iterate over prev.prev nodes."""
        node: Node[T] | None = self.prev
        while node is not None:
            yield node
            node = node.prev


NULL_NODE: Node[Any] = Node(value="__NULL__")


Direction = Literal["next", "prev"]
