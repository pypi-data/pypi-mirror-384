from __future__ import annotations

import pytest

from bear_dereth.data_structs.linked_lists.nodes import NULL_NODE, Node


def test_node_linking_and_iteration() -> None:
    first = Node(1)
    second = Node(2)
    third = Node(3)

    first.next = second
    second.prev = first
    second.next = third
    third.prev = second

    assert first.is_linked
    assert not first.is_unlinked
    assert [node.value for node in first] == [2, 3]
    assert [node.value for node in reversed(third)] == [2, 1]


def test_node_null_sentinel_properties() -> None:
    assert NULL_NODE.is_null
    assert not NULL_NODE.is_not_null

    with pytest.raises(AttributeError):
        NULL_NODE.value = "changed"


def test_node_is_unlinked_state() -> None:
    node = Node("data")
    assert node.is_unlinked

    linked = Node("left", next=node)
    node.prev = linked

    assert node.is_linked
    assert linked.is_linked
