from __future__ import annotations

import pytest

from bear_dereth.data_structs.counter_class import Counter


def test_counter_tick_and_reset_behaviour() -> None:
    counter = Counter(start=2)

    assert counter.get() == 2
    assert next(counter) == 3

    counter.reset(5)
    assert counter.get() == 5

    assert counter.get(before=True) == 6
    assert counter.get(after=True) == 6
    assert counter.get() == 7


def test_counter_set_and_comparison_operations() -> None:
    counter = Counter()
    counter.set(4)

    assert counter == 4
    assert counter < 6
    assert counter <= 4
    assert counter > 2
    assert counter >= 4

    with pytest.raises(ValueError, match="Counter value cannot be negative"):
        counter.set(-1)

    with pytest.raises(ValueError, match="Cannot set counter to a value less than the current counter value"):
        counter.set(3)


def test_counter_clone_creates_independent_copy() -> None:
    counter = Counter(start=1)
    clone = counter.clone()

    assert clone is not counter
    assert clone.count == counter.count

    counter.tick()
    assert clone.count != counter.count
