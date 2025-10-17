"""A simple linked list implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from bear_dereth.data_structs.cursor import BaseCursor
from bear_dereth.data_structs.linked_lists.doubly import DoublyLinkedList
from bear_dereth.data_structs.linked_lists.nodes import Node

if TYPE_CHECKING:
    from collections.abc import Iterator

    from bear_dereth.query import QueryProtocol


class NodeCursor[T](BaseCursor[DoublyLinkedList[T], Node[T]]):
    """A cursor to track a position in a linked list using BaseCursor."""

    def __init__(self) -> None:
        """Initialize an empty NodeCursor."""
        super().__init__(DoublyLinkedList, None)

    @property
    def collection(self) -> DoublyLinkedList[T]:
        """Get the current linked list collection."""
        return super().collection

    @property
    def head_node(self) -> Node[T] | None:
        """Node at the head of the list."""
        return self.collection.head

    @property
    def tail_node(self) -> Node[T] | None:
        """Node at the tail of the list."""
        return self.collection.tail

    @property
    def size(self) -> int:
        """Get the current size of the linked list."""
        return super().size

    def update_tail(self, new_tail: Node[T]) -> None:
        """Attach a new tail node."""
        was_empty: bool = self.is_empty
        self.collection.append(new_tail)
        if was_empty:
            self.set_index(0)
        else:
            self.set_index(self.index)

    def update_head(self, new_head: Node[T]) -> None:
        """Attach a new head node."""
        was_empty: bool = self.is_empty
        self.collection.appendleft(new_head)
        if was_empty:
            self.set_index(0)
        else:
            self.set_index(self.index + 1)

    def pop_head(self) -> Node[T] | None:
        """Pop the head node and return it."""
        previous_index: int = self.index
        node: Node[T] = self.collection.pop(head=True)
        if self.is_empty:
            self.set_index(0)
        else:
            self.set_index(previous_index - 1)
        return node

    def pop_tail(self) -> Node[T] | None:
        """Pop the tail node and return it."""
        previous_index: int = self.index
        node: Node[T] = self.collection.pop(head=False)
        if self.not_empty:
            self.set_index(min(previous_index, self.upper))
        else:
            self.set_index(0)
        return node

    def jump_to_head(self) -> None:
        """Move the cursor to the head node."""
        super().head()

    def jump_to_tail(self) -> None:
        """Move the cursor to the tail node."""
        super().tail()

    def jump_to_index(self, index: int) -> None:
        """Move the cursor to a specific index."""
        if index < 0 or index >= self.size:
            raise IndexError("Index out of bounds")
        self.set_index(index)

    def get(self, offset: int | None = None) -> Node[T]:
        """Return the node at the current cursor position."""
        return super().get(offset)

    def current_index(self) -> int:
        """Return the current index of the cursor."""
        return self.index

    def index_of(self, node: Node[T]) -> int:
        """Find the index of a node."""
        return self.collection.index_of(node)

    def clear(self) -> None:
        """Clear the collection."""
        self.collection.clear()
        self.set_index(0)

    def traverse(self) -> Iterator[Node[T]]:
        """Iterate from head to tail."""
        yield from iter(self.collection)

    def reverse(self) -> Iterator[Node[T]]:
        """Iterate from tail to head."""
        yield from reversed(self.collection)

    def search(self, func: QueryProtocol) -> Node[T] | None:
        """Search for a node that matches a given condition."""
        for node in self.collection:
            if func(node.value):
                return node
        return None


class LinkedList[T]:
    """A simple linked list implementation."""

    def __init__(self) -> None:
        """Initialize an empty linked list."""
        self.cursor: NodeCursor[T] = NodeCursor()

    def push(self, value: T) -> None:
        """Push a value onto the end of the list."""
        new_node: Node[T] = Node(value)
        self.cursor.update_tail(new_node)

    def pop(self) -> T | None:
        """Pop a value off the end of the list."""
        popped_node: Node[T] | None = self.cursor.pop_tail()
        return popped_node.value if popped_node is not None else None

    def shift(self) -> T | None:
        """Pop a value off the start of the list."""
        popped_node: Node[T] | None = self.cursor.pop_head()
        return popped_node.value if popped_node is not None else None

    def unshift(self, value: T) -> None:
        """Push a value onto the start of the list."""
        new_node: Node[T] = Node(value)
        self.cursor.update_head(new_node)

    def peek(self) -> T | None:
        """Peek at the value at the end of the list without removing it."""
        if self.cursor.tail_node is not None:
            return self.cursor.tail_node.value
        return None

    def peek_head(self) -> T | None:
        """Peek at the value at the start of the list without removing it."""
        if self.cursor.head_node is not None:
            return self.cursor.head_node.value
        return None

    def peek_n(self, n: int) -> T | None:
        """Peek at the value at the nth index of the list without removing it."""
        if n < 0 or n >= self.cursor.size:
            raise IndexError("Index out of bounds")
        self.cursor.jump_to_index(n)
        if self.cursor.current is not None:
            return self.cursor.current.value
        return None

    def clear(self) -> None:
        """Clear the list."""
        self.cursor.clear()

    def is_empty(self) -> bool:
        """Check if the list is empty."""
        return self.cursor.size == 0

    def to_list(self) -> list[T]:
        """Convert the linked list to a standard Python list."""
        return list(self)

    @classmethod
    def from_list(cls, values: list[T]) -> LinkedList[T]:
        """Create a linked list from a standard Python list."""
        ll: LinkedList[T] = cls()
        for value in values:
            ll.push(value)
        return ll

    @property
    def head(self) -> T | None:
        """Get the value at the head of the list."""
        return self.peek_head()

    @property
    def tail(self) -> T | None:
        """Get the value at the tail of the list."""
        return self.peek()

    @property
    def size(self) -> int:
        """Get the size of the list."""
        return len(self)

    def traverse(self, reverse: bool = False) -> Iterator[T]:
        """Traverse the list from head to tail."""
        if reverse:
            yield from self.__reversed__()
        else:
            yield from self.__iter__()

    def search(self, func: QueryProtocol) -> T | None:
        """Search for a value in the list that matches a given condition."""
        node: Node[T] | None = self.cursor.search(func)
        return node.value if node is not None else None

    def index_of(self, value: T) -> int:
        """Get the index of a value in the list, or -1 if not found."""
        return self.cursor.index_of(Node(value))

    def combine(self, other: LinkedList[T]) -> None:
        """Combine another linked list into this one."""
        if not isinstance(other, LinkedList):
            raise TypeError("Can only combine with another LinkedList")
        if other.is_empty():
            return
        values: list[T] = list(other)
        for value in values:
            self.push(value)
        if other is not self:
            other.clear()

    def __hash__(self) -> int:
        """Hash based on values in the list."""
        return hash(tuple(self))

    def __eq__(self, other: object) -> bool:
        """Check equality based on values in the list."""
        if not isinstance(other, LinkedList):
            return NotImplemented
        if len(self) != len(other):
            return False
        return all(a == b for a, b in zip(self, other, strict=False))

    def __ne__(self, other: object) -> bool:
        """Check inequality based on values in the list."""
        if not isinstance(other, LinkedList):
            return NotImplemented
        return not self == other

    def __lt__(self, other: LinkedList[T]) -> bool:
        """Check if this list is less than another list based on values."""
        if not isinstance(other, LinkedList):
            return NotImplemented
        return list(self) < list(other)

    def __le__(self, other: LinkedList[T]) -> bool:
        """Check if this list is less than or equal to another list based on values."""
        if not isinstance(other, LinkedList):
            return NotImplemented
        return list(self) <= list(other)

    def __gt__(self, other: LinkedList[T]) -> bool:
        """Check if this list is greater than another list based on values."""
        if not isinstance(other, LinkedList):
            return NotImplemented
        return list(self) > list(other)

    def __ge__(self, other: LinkedList[T]) -> bool:
        """Check if this list is greater than or equal to another list based on values."""
        if not isinstance(other, LinkedList):
            return NotImplemented
        return list(self) >= list(other)

    def __contains__(self, value: T) -> bool:
        """Check if the list contains a value."""
        return any(item == value for item in self)

    def __getitem__(self, n: int) -> T | None:
        """Get the value at the nth index of the list."""
        return self.peek_n(n)

    def __slice__(self, s: slice) -> LinkedList[T]:
        """Get a slice of the list as a new LinkedList."""
        start, stop, step = s.indices(self.cursor.size)
        new_list: LinkedList[T] = LinkedList[T]()
        for i in range(start, stop, step):
            value: T | None = self.peek_n(i)
            if value is not None:
                new_list.push(value)
        return new_list

    def __setitem__(self, n: int, value: T) -> None:
        """Set the value at the nth index of the list."""
        if n < 0 or n >= self.cursor.size:
            raise IndexError("Index out of bounds")
        self.cursor.jump_to_index(n)
        if self.cursor.current is not None:
            self.cursor.current.value = value

    def __len__(self) -> int:
        """Get the length of the list."""
        return self.cursor.size

    def __iter__(self) -> Iterator[T]:
        """Iterate over the values in the list."""
        yield from (node.value for node in self.cursor.traverse())

    def __reversed__(self) -> Iterator[T]:
        """Iterate over the values in the list in reverse order."""
        yield from (node.value for node in self.cursor.reverse())

    def __bool__(self) -> bool:
        """Check if the list is non-empty."""
        return not self.is_empty()

    def __str__(self) -> str:
        """Get a string representation of the list."""
        return "LinkedList([" + ", ".join(str(value) for value in self) + "])"

    def __repr__(self) -> str:
        """Get a detailed string representation of the list."""
        return f"<LinkedList size={self.cursor.size} head={self.cursor.head_node} tail={self.cursor.tail_node}>"
