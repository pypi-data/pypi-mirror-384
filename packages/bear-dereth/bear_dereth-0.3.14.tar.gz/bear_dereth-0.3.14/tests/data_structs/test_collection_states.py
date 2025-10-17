from __future__ import annotations

from dataclasses import dataclass

from bear_dereth.data_structs.collection_states import CollectionStates, State
from bear_dereth.data_structs.cursor import CollectionProtocol

# ruff: noqa: D102


@dataclass
class DummyCollection(CollectionProtocol):
    items: list[int]

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index: int) -> int:
        return self.items[index]

    def __setitem__(self, index: int, value: int) -> None:
        self.items[index] = value

    def pop(self) -> int:
        return self.items.pop()

    def remove(self, item: int) -> None:
        self.items.remove(item)

    def get(self, index: int) -> int:
        return self.items[index]

    def copy(self) -> DummyCollection:
        return DummyCollection(self.items.copy())

    def clear(self) -> None:
        self.items.clear()

    def join(self, d: str) -> str:
        return d.join(str(i) for i in self.items)


def test_collection_states_push_and_pop_state() -> None:
    collection = DummyCollection([1, 2, 3])
    states: CollectionStates[DummyCollection] = CollectionStates()

    states.push_state("initial", index=1, collection=collection)
    saved_state = states.pop_state("initial")

    assert isinstance(saved_state, State)
    assert saved_state.name == "initial"
    assert saved_state.index == 1
    assert saved_state.collection.items == [1, 2, 3]

    # Original collection mutated after saving should not affect saved snapshot
    collection.items.append(4)
    assert saved_state.collection.items == [1, 2, 3]


def test_collection_states_missing_state_returns_none() -> None:
    states: CollectionStates[DummyCollection] = CollectionStates()
    assert states.pop_state("missing") is None
