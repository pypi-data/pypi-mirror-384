"""Doubly linked list implementation."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from bear_dereth.data_structs.linked_lists.nodes import NULL_NODE, Direction, Node

if TYPE_CHECKING:
    from collections.abc import Iterator

    from bear_dereth.query import QueryProtocol


class DoublyLinkedList[T]:
    """Internal doubly-linked collection that powers NodeCursor."""

    def __init__(self) -> None:
        """Initialize an empty doubly linked list."""
        self._head: Node[T] | None = None
        self._tail: Node[T] | None = None
        self._size: int = 0

    def update(
        self,
        head: Node[T] | None = NULL_NODE,
        tail: Node[T] | None = NULL_NODE,
        size: int | None = None,
    ) -> None:
        """Update the linked list data."""
        if head is not NULL_NODE:
            self._head = head
        if tail is not NULL_NODE:
            self._tail = tail
        if size is not None:
            self._size = size

    def plus(self) -> None:
        """Increment the size of the linked list."""
        self._size += 1

    def minus(self) -> None:
        """Decrement the size of the linked list."""
        self._size -= 1

    def size(self) -> int:
        """Get the current size of the linked list."""
        return self._size

    @property
    def head(self) -> Node[T] | None:
        """Get the head of the linked list."""
        return self._head

    @property
    def tail(self) -> Node[T] | None:
        """Get the tail of the linked list."""
        return self._tail

    def within_bounds(self, index: int) -> bool:
        """Check if an index is within the bounds of the linked list."""
        return 0 <= index < self._size

    def within_first_half(self, index: int) -> bool:
        """Check if an index is within the first half of the linked list."""
        return 0 <= index < (self._size // 2)

    def pop(self, head: bool = False) -> Node[T]:
        """Pop an item off the end of the linked list. Raises IndexError if the list is empty."""
        node: Node[T] | None = self._pop(head=head)
        if node is None:
            raise IndexError("pop from empty linked list")
        return node

    def _pop(self, head: bool = False) -> Node[T] | None:
        if head:
            if self._head is None:
                return None
            node: Node[T] = self._head
            self.remove(node)
            return node
        if self._tail is None:
            return None
        node: Node[T] = self._tail
        self.remove(node)
        return node

    def remove(self, item: Node[T]) -> None:
        """Remove a specific node from the linked list."""
        if self.is_empty:
            raise ValueError("cannot remove from empty linked list")
        if item.prev is None:
            self.update(head=item.next)
        else:
            item.prev.next = item.next
        if item.next is None:
            self.update(tail=item.prev)
        else:
            item.next.prev = item.prev
        item.prev = None
        item.next = None
        self.minus()

    def get(self, index: int) -> Node[T]:
        """Get an item from the linked list by index."""
        return self._node_at(index)

    def set(self, index: int, value: T) -> None:
        """Set the value of a node at a specific index in the linked list."""
        target: Node[T] = self._node_at(index)
        target.value = value

    def copy(self) -> list[T]:
        """Get a copy of the current linked list as a list of values."""
        return [node.value for node in self]

    def clear(self) -> None:
        """Clear all items from the linked list."""
        node: Node[T] | None = self._head
        while node is not None:
            nxt: Node[T] | None = node.next
            node.prev = None
            node.next = None
            node = nxt
        self.update(head=None, tail=None, size=0)

    def append(self, item: Node[T]) -> None:
        """Append a node to the end of the linked list."""
        self._detach(item)
        item.prev = self._tail
        item.next = None
        if self._tail is not None:
            self._tail.next = item
        else:
            self.update(head=item)
        self.update(tail=item)
        self.plus()

    def appendleft(self, item: Node[T]) -> None:
        """Append a node to the start of the linked list."""
        self._detach(item)
        item.next = self._head
        item.prev = None
        if self._head is not None:
            self._head.prev = item
        else:
            self.update(tail=item)
        self.update(head=item)
        self.plus()

    def index_of(self, item: Node[T]) -> int:
        """Get the index of a specific item in the linked list, or -1 if not found."""
        values: tuple[int, Node[T] | None] = self.find_by_value(item.value)
        return values[0]

    def find_by_value(self, value: T) -> tuple[int, Node[T] | None]:
        """Find a node by its value in the linked list.

        Args:
            value (T): The value to find.

        Returns:
            tuple[int, Node[T] | None]: A tuple containing the index of the node and the node itself, or (-1, None) if not found.
        """
        current: Node[T] | None = self._head
        idx: int = 0
        while current is not None:
            if current.value == value:
                return idx, current
            current = current.next
            idx += 1
        return -1, None

    def find_by_index(self, n: Node[T] | None, c: int, d: Direction) -> Node[T]:
        """Find a node by its index in the linked list.

        Args:
            n (Node[T] | None): The starting node (head or tail).
            c (int): The index to find.
            d (Direction): The direction to traverse ("next" or "prev").

        Returns:
            Node[T]: The node at the specified index.

        Raises:
            IndexError: If the index is out of bounds.
        """
        if n is None:
            raise IndexError("Index out of bounds")
        nodes: Iterator[Node[T]] = reversed(n) if d == "prev" else iter(n)
        for _ in range(c):
            n = next(nodes)
        return n

    def iter_nodes(self) -> Iterator[Node[T]]:
        """Iterate over the nodes in the linked list from head to tail."""
        yield from self.__iter__()

    def iter_nodes_reverse(self) -> Iterator[Node[T]]:
        """Iterate over the nodes in the linked list from tail to head."""
        yield from self.__reversed__()

    def _node_at(self, index: int) -> Node[T]:
        if not self.within_bounds(index):
            raise IndexError("Index out of bounds")
        if self.within_first_half(index):
            node: Node[T] = self.find_by_index(self._head, index, "next")
        else:
            node: Node[T] = self.find_by_index(self._tail, self._size - 1 - index, "prev")
        return node

    @staticmethod
    def _detach(node: Node[T]) -> None:
        node.prev = None
        node.next = None

    @property
    def is_empty(self) -> bool:
        """Check if the linked list is empty."""
        return self._size == 0

    def iter_next(self, start: Node[T] | None = None) -> Iterator[Node[T]]:
        """Iterate over the nodes in the linked list from a starting node to the end."""
        node: Node[T] | None = start if start is not None else self._head
        while node is not None:
            yield node
            node = node.next

    def iter_prev(self, start: Node[T] | None = None) -> Iterator[Node[T]]:
        """Iterate over the nodes in the linked list from a starting node to the beginning."""
        node: Node[T] | None = start if start is not None else self._tail
        while node is not None:
            yield node
            node = node.prev

    def search(self, func: QueryProtocol) -> Node[T] | None:
        """Search for the first node matching the predicate."""
        for node in iter(self):
            if func(node.value):
                return node
        return None

    def join(self, d: str = ", ") -> str:
        """Join the linked list node values into a single string with the given delimiter.

        Args:
            d (str): The delimiter to use between items. Defaults to ", ".

        Returns:
            str: The joined string of node values.
        """
        return d.join(str(node.value) for node in self) if not self.is_empty else ""

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[Node[T]]:
        yield from self.iter_next()

    def __reversed__(self) -> Iterator[Node[T]]:
        yield from self.iter_prev()

    def __getitem__(self, index: int) -> Node[T]:
        return self._node_at(index)

    def __setitem__(self, index: int, value: T) -> None:
        target: Node[T] = self._node_at(index)
        target.value = value
