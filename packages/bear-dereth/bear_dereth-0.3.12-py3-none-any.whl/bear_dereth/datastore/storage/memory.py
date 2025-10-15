"""In-memory storage backend for the datastore."""

from collections.abc import Callable
from pathlib import Path

from bear_dereth.datastore.unified_data import UnifiedDataFormat

from .base_storage import Storage


class InMemoryStorage(Storage):
    """Simple in-memory storage backend for testing or temporary data."""

    class _Handle:
        def __init__(self, closer: Callable[[], None] | None = None) -> None:
            self.clear_callback: Callable[[], None] | None = closer

        def clear(self) -> None:
            if self.clear_callback is not None:
                self.clear_callback()
                self.clear_callback = None

    def __init__(self, file: str | Path | None = None, data: UnifiedDataFormat | None = None) -> None:
        """Initialize empty in-memory storage."""
        super().__init__()
        self.file: Path = Path.cwd() if file is None else Path(file)
        self.handle = self._Handle(self.close)
        self._data: UnifiedDataFormat = data if data is not None else UnifiedDataFormat()

    def read(self) -> UnifiedDataFormat:
        """Read data from memory.

        Returns:
            Stored data or None if empty
        """
        return self._data

    def write(self, data: UnifiedDataFormat) -> None:
        """Write data to memory.

        Args:
            data: Data to store
        """
        self._data = data

    def close(self) -> None:
        """Clear the stored data."""
        if self._data is not None:
            self._data.clear()

    @property
    def closed(self) -> bool:
        """Check if the storage is closed (empty)."""
        return self._data is None


__all__ = ["InMemoryStorage"]
