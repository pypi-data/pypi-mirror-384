"""A Simple Stack implementation."""

from __future__ import annotations

from bear_dereth.data_structs.collection_states import CollectionStates, State
from bear_dereth.data_structs.stacks.with_cursor import SimpleStackCursor


class FancyStack[T](SimpleStackCursor[T]):
    """A simple stack implementation with a cursor and state management."""

    def __init__(self, data: T | None = None) -> None:
        """Initialize an empty stack."""
        super().__init__(data)
        self.states: CollectionStates[SimpleStackCursor] = CollectionStates()

    def save_state(self, name: str) -> None:
        """Save the current state of the stack to a cursor with a given name.

        Args:
            name (str): The name to save the state under.

        Returns:
            bool: True if the state was saved, False otherwise.
        """
        self.states.push_state(name, self.index, self.stack)

    def load_state(self, name: str):
        """Load a saved state of the stack from the cursor by name.

        Args:
            name (str): The name of the saved state to load.

        Returns:
            bool: True if the state was loaded, False if not found.
        """
        state: State[SimpleStackCursor] | None = self.states.pop_state(name)
        if state is None:
            return False
        self._update(state.collection)
        self.index = state.index
        return True
