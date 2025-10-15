from __future__ import annotations

import pytest

from bear_dereth.data_structs.linked_lists.doubly import DoublyLinkedList
from bear_dereth.data_structs.linked_lists.nodes import Node


def build_list(values: list[int]) -> tuple[DoublyLinkedList[int], list[Node[int]]]:
    dll = DoublyLinkedList[int]()
    nodes = [Node(value) for value in values]
    for node in nodes:
        dll.append(node)
    return dll, nodes


def test_doubly_linked_list_append_and_iteration() -> None:
    dll, nodes = build_list([1, 2, 3])

    assert dll.head is nodes[0]
    assert dll.tail is nodes[-1]
    assert [node.value for node in dll.iter_nodes()] == [1, 2, 3]
    assert [node.value for node in dll.iter_nodes_reverse()] == [3, 2, 1]

    dll.appendleft(Node(0))
    assert dll.head.value == 0
    assert [node.value for node in dll] == [0, 1, 2, 3]


def test_doubly_linked_list_pop_remove_and_indexing() -> None:
    dll, _ = build_list([10, 20, 30])

    head = dll.pop(head=True)
    assert head.value == 10
    assert dll.head.value == 20

    tail = dll.pop()
    assert tail.value == 30
    assert dll.tail.value == 20

    last = dll.pop()
    assert last.value == 20

    with pytest.raises(IndexError):
        dll.pop()

    dll.append(Node(40))
    dll.append(Node(50))
    dll.append(Node(60))
    middle = dll[1]
    dll.remove(middle)
    assert [node.value for node in dll] == [40, 60]


def test_doubly_linked_list_find_and_join_helpers() -> None:
    dll, _ = build_list([1, 2, 3, 2])

    idx, found = dll.find_by_value(2)
    assert idx == 1
    assert found is dll[1]

    assert dll.find_by_value(99) == (-1, None)

    assert dll.join("-") == "-".join(str(value) for value in [1, 2, 3, 2])


def test_doubly_linked_list_set_and_copy() -> None:
    dll, _ = build_list([5, 6, 7])
    dll.set(1, 99)
    assert dll[1].value == 99

    assert dll.copy() == [5, 99, 7]


def test_doubly_linked_list_bounds_checks() -> None:
    dll = DoublyLinkedList[int]()

    with pytest.raises(IndexError):
        _ = dll[0]

    dll.append(Node(1))

    with pytest.raises(IndexError):
        dll._node_at(2)  # type: ignore[attr-defined]

    dll.clear()
    assert dll.is_empty
