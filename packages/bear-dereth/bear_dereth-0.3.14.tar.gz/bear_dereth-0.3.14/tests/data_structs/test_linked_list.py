from __future__ import annotations

import pytest

from bear_dereth.data_structs.linked_lists.linked_list import LinkedList, Node, NodeCursor


def test_linked_list_push_pop_and_shift_operations() -> None:
    linked: LinkedList[int] = LinkedList()

    linked.push(1)
    linked.push(2)
    linked.unshift(0)

    assert list(linked) == [0, 1, 2]
    assert linked.peek() == 2
    assert linked.peek_head() == 0

    assert linked.pop() == 2
    assert linked.shift() == 0
    assert list(linked) == [1]


def test_linked_list_combination_and_search() -> None:
    linked_a: LinkedList[str] = LinkedList.from_list(["a", "b"])
    linked_b: LinkedList[str] = LinkedList.from_list(["c", "d"])

    linked_a.combine(linked_b)
    assert list(linked_a) == ["a", "b", "c", "d"]
    assert linked_b.is_empty()

    assert linked_a.search(lambda value: value == "c") == "c"
    assert linked_a.index_of("d") == 3
    assert "b" in linked_a
    assert linked_a[1] == "b"


def test_linked_list_slice_and_setitem() -> None:
    linked = LinkedList.from_list([1, 2, 3, 4, 5])

    sliced = linked.__slice__(slice(1, 4, 2))
    assert list(sliced) == [2, 4]

    linked[2] = 99
    assert list(linked) == [1, 2, 99, 4, 5]


def test_node_cursor_navigation_and_search() -> None:
    cursor: NodeCursor[int] = NodeCursor()
    cursor.update_tail(Node(10))
    cursor.update_tail(Node(20))
    cursor.update_tail(Node(30))

    assert cursor.head_node.value == 10
    assert cursor.tail_node.value == 30
    assert cursor.current.value == 10

    cursor.tick()
    assert cursor.current.value == 20
    cursor.tail()
    assert cursor.current.value == 30

    node = cursor.search(lambda value: value == 20)
    assert node is not None
    assert node.value == 20

    popped = cursor.pop_head()
    assert popped.value == 10

    assert cursor.index_of(Node(20)) == 0


def test_linked_list_clear_and_to_list() -> None:
    linked = LinkedList.from_list([1, 2, 3])
    assert linked.to_list() == [1, 2, 3]

    linked.clear()
    assert linked.is_empty()
    assert list(linked) == []

    with pytest.raises(IndexError):
        linked.peek_n(0)
