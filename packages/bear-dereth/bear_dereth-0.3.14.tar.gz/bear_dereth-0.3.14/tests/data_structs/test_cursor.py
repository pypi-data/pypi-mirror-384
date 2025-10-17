from __future__ import annotations

from typing import Any

import pytest

from bear_dereth.data_structs.cursor import BaseCursor, CollectionProtocol
from bear_dereth.data_structs.stacks.with_cursor import SimpleStackCursor

# ruff: noqa: D102


class ListCollection(list, CollectionProtocol):
    def remove(self, item: Any) -> None:
        self.remove(item)

    def get(self, index: int):
        return self[index]

    def copy(self):
        return list(self)

    def join(self, d: str):
        return d.join(str(item) for item in self)


def test_base_cursor_navigation_and_bounds() -> None:
    cursor = BaseCursor(ListCollection, default=None)
    cursor.push(10)
    cursor.push(20)
    cursor.push(30)

    assert cursor.current == 10
    cursor.tick()
    assert cursor.current == 20

    cursor.tail()
    assert cursor.current == 30
    cursor.head()
    assert cursor.current == 10

    cursor.offset(2)
    assert cursor.current == 30
    assert cursor.get(-2) == 10

    with pytest.raises(IndexError):
        empty = BaseCursor(ListCollection, default=None).pop()


def test_base_cursor_join_and_clear() -> None:
    cursor = BaseCursor(ListCollection, default="")
    cursor.push("a")
    cursor.push("b")

    assert cursor.join("-") == "a-b"
    assert cursor.copy() == ["a", "b"]

    cursor.clear()
    assert cursor.is_empty
    assert cursor.join() == ""


def test_simple_stack_cursor_attributes() -> None:
    stack: SimpleStackCursor[int] = SimpleStackCursor[int]()
    dupes: list[str] = SimpleStackCursor.duplicates
    assert not dupes, f"Duplicate attributes found: {dupes}"
    fields: dict[str, list[str]] = SimpleStackCursor.fields
    assert "collection" in fields
    assert "handler" in fields
    assert "push" in fields["handler"]
    assert "pop" in fields["handler"]
    assert "join" in fields["collection"]
    assert "remove" in fields["collection"]
    assert "get" in fields["handler"]
