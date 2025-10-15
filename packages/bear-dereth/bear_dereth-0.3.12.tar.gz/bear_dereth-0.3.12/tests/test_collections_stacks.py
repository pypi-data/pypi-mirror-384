from __future__ import annotations

import pytest

from bear_dereth.data_structs.collection_states import CollectionStates, State
from bear_dereth.data_structs.cursor import BaseCursor
from bear_dereth.data_structs.stacks.better import FancyStack
from bear_dereth.data_structs.stacks.simple import SimpleStack
from bear_dereth.data_structs.stacks.with_cursor import SimpleStackCursor


class AppendableIntStack(SimpleStack[int]):
    """Extend SimpleStack with an append method for BaseCursor tests."""

    def append(self, item: int) -> None:
        """Append is an alias for push."""
        super().push(item)


class AppendableStrStack(SimpleStack[str]):
    """String version of AppendableIntStack for join behaviour tests."""

    def append(self, item: str) -> None:
        """Append is an alias for push."""
        super().push(item)


def test_simple_stack_basic_operations() -> None:
    stack: SimpleStack[int] = SimpleStack()
    assert stack.is_empty

    stack.push(1)
    stack.push(2)

    assert stack.size == 2
    assert stack.not_empty
    assert stack.has(1)
    assert 1 in stack
    assert stack.get(0) == 1
    assert stack[1] == 2
    assert stack.__slice__(0, 2) == [1, 2]

    snapshot: list[int] = stack.copy()
    assert snapshot == [1, 2]
    assert snapshot is not stack.stack

    stack.remove(1)
    assert 1 not in stack
    assert stack.size == 1
    assert stack.pop() == 2
    assert stack.is_empty

    with pytest.raises(IndexError):
        stack.pop()


def test_simple_stack_cursor_navigation_and_clear() -> None:
    cursor: SimpleStackCursor[int] = SimpleStackCursor()
    cursor.push(10)
    cursor.push(20)
    cursor.push(30)

    assert isinstance(cursor.stack, SimpleStack)
    assert cursor.size == 3
    assert cursor.current == 10

    cursor.tick()
    assert cursor.current == 20

    cursor.tail()
    assert cursor.current == 30

    cursor.tock()
    assert cursor.current == 20
    assert cursor.peek(head=True) == 10
    assert cursor.peek(tail=True) == 30

    cursor.clear()
    assert cursor.is_empty
    assert cursor.peek() is None

    with pytest.raises(AttributeError):
        _ = cursor.not_a_real_attribute  # type: ignore[attr-defined]


def test_simple_stack_cursor_fields_and_join() -> None:
    cursor: SimpleStackCursor[str] = SimpleStackCursor()
    fields: dict[str, list[str]] = cursor.fields

    assert set(fields.keys()) == {"collection", "handler"}
    assert "push" in fields["collection"]
    assert "tick" in fields["handler"]

    cursor.push("alpha")
    cursor.push("beta")
    assert cursor.join(" | ") == "alpha | beta"

    numeric_cursor: SimpleStackCursor[int] = SimpleStackCursor()
    numeric_cursor.push(1)

    value = numeric_cursor.join()
    assert value == "1"
    assert isinstance(value, str)


def test_collection_states_store_independent_copies() -> None:
    stack: SimpleStack[int] = SimpleStack()
    stack.push(1)

    states: CollectionStates[SimpleStack] = CollectionStates()
    states.push_state("initial", 0, stack)

    stack.push(99)
    state: State[SimpleStack] | None = states.pop_state("initial")

    assert state is not None
    assert state.name == "initial"
    assert state.index == 0
    assert state.collection == [1]
    assert states.pop_state("missing") is None


def test_collection_states_replaces_existing_state() -> None:
    stack: SimpleStack[int] = SimpleStack()
    stack.push(5)

    states: CollectionStates[SimpleStack] = CollectionStates()
    states.push_state("snapshot", 0, stack)

    stack.push(10)
    states.push_state("snapshot", 1, stack)

    state: State[SimpleStack] | None = states.pop_state("snapshot")
    assert state is not None
    assert state.index == 1
    assert state.collection == [5, 10]


def test_fancy_stack_save_and_load_state_restores_snapshot() -> None:
    fancy: FancyStack[int] = FancyStack()
    fancy.push(1)
    fancy.push(2)
    fancy.tick()
    fancy.save_state("snapshot")

    fancy.pop()
    fancy.push(99)
    assert fancy.size == 2

    assert fancy.load_state("snapshot") is True
    assert fancy.size == 2
    assert fancy.peek(head=True) == 1
    assert fancy.peek(tail=True) == 2
    assert list(fancy.stack) == [1, 2]

    assert fancy.load_state("nope") is False


def test_base_cursor_navigation_with_appendable_stack() -> None:
    cursor: BaseCursor[AppendableIntStack, int] = BaseCursor(AppendableIntStack, default=-1)

    assert cursor.is_empty
    assert cursor.get() == -1

    cursor.push(5)
    cursor.push(10)
    assert len(cursor) == 2
    assert cursor.current == 5
    assert cursor.within_bounds

    cursor.tick()
    assert cursor.current == 10

    cursor.offset(100)
    assert cursor.current == 10  # clamped to upper bound

    cursor.tock()
    assert cursor.current == 5

    cursor.tail()
    assert cursor.index == 1

    cursor.head()
    assert cursor.index == 0

    cursor.set_index(10)
    assert cursor.index == 1

    with pytest.raises(ValueError):  # noqa: PT011
        cursor.index = 0

    assert cursor.pop() == 10
    assert len(cursor) == 1

    cursor.clear()
    assert cursor.is_empty
    assert cursor.peek() == -1

    with pytest.raises(IndexError):
        cursor.pop()

    with pytest.raises(ValueError):  # noqa: PT011
        cursor.peek(head=True, tail=True)


def test_base_cursor_join_and_copy_behaviour() -> None:
    class Test: ...

    test = Test()
    cursor: BaseCursor[AppendableStrStack, str] = BaseCursor(AppendableStrStack, default="")
    cursor.push("a")
    cursor.push("b")
    assert cursor.join("-") == "a-b"
    assert cursor.copy() == ["a", "b"]

    numeric_cursor: BaseCursor[AppendableIntStack, int] = BaseCursor(AppendableIntStack, default=-1)
    numeric_cursor.push(5)
    numeric_cursor.push(10)
