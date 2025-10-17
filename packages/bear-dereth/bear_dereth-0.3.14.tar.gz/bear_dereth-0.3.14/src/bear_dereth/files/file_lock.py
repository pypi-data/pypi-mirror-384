"""Context manager for file locking using fcntl."""

from __future__ import annotations

import fcntl
from typing import IO, Any, Self

EXCLUSIVE_LOCK: int = fcntl.LOCK_EX
SHARED_LOCK: int = fcntl.LOCK_SH
UNLOCK: int = fcntl.LOCK_UN


class FileLock:
    """Context manager for file locking using fcntl."""

    def __init__(self, handle: IO[Any], exclusive: bool = True) -> None:
        """Initialize the file lock."""
        self.handle: IO[Any] = handle
        self.lock_type: int = EXCLUSIVE_LOCK if exclusive else SHARED_LOCK

    def flock(self, handle: IO[Any], operation: int) -> None:
        """Apply a file lock operation on the given file handle."""
        fcntl.flock(handle.fileno(), operation)

    def __enter__(self) -> Self:
        self.flock(handle=self.handle, operation=self.lock_type)
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.flock(handle=self.handle, operation=UNLOCK)


class LockEx(FileLock):
    """Context manager for exclusive file locking."""

    def __init__(self, handle: IO[Any]) -> None:
        """Initialize exclusive file lock."""
        super().__init__(handle, exclusive=True)


class LockSh(FileLock):
    """Context manager for shared file locking."""

    def __init__(self, handle: IO[Any]) -> None:
        """Initialize shared file lock."""
        super().__init__(handle, exclusive=False)
