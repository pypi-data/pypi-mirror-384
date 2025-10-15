"""Abstract base class for all storage backends."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Storage[T](ABC):
    """Abstract base class for all storage backends.

    A Storage handles serialization/deserialization of database state
    to/from various backends (files, memory, etc.).
    """

    @abstractmethod
    def read(self) -> T:
        """Read the current state from storage.

        Any kind of deserialization should go here.

        Returns:
            Loaded data or None if storage is empty.
        """
        raise NotImplementedError("To be overridden!")

    @abstractmethod
    def write(self, data: T) -> None:
        """Write the current state to storage.

        Any kind of serialization should go here.

        Args:
            data: The current state of the database.
        """
        raise NotImplementedError("To be overridden!")

    def clear(self) -> None:
        """Clear all data from the storage."""
        self.handler.clear()

    @abstractmethod
    def close(self) -> None:
        """Close open file handles or cleanup resources."""

    @property
    @abstractmethod
    def closed(self) -> bool:
        """Check if the storage is closed."""
        raise NotImplementedError("To be overridden!")

    def __getattr__[V](self, name: str) -> V:  # pyright: ignore[reportInvalidTypeVarUse]
        """Forward all unknown attribute calls to the underlying storage."""
        return getattr(self, name)
