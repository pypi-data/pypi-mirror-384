"""A handler for saving and loading states of a collection."""

from __future__ import annotations

from dataclasses import dataclass, field

from bear_dereth.data_structs.cursor import CollectionProtocol


@dataclass(slots=True)
class State[CollectionType: CollectionProtocol]:
    """A saved state of the stack."""

    name: str
    collection: CollectionType
    index: int = -1


@dataclass(slots=True)
class CollectionStates[Collection_T: CollectionProtocol]:
    """A handler for saving and loading states of a collection."""

    states: dict[str, State[Collection_T]] = field(default_factory=dict)

    def push_state(self, name: str, index: int, collection: CollectionProtocol) -> None:
        """Save the current state of the collection to a state with a given name."""
        state: State[Collection_T] = State(
            name=name,
            index=index,
            collection=collection.copy(),
        )
        self.states[name] = state

    def pop_state(self, name: str) -> State[Collection_T] | None:
        """Load a saved state of the collection by name."""
        return self.states.get(name)
