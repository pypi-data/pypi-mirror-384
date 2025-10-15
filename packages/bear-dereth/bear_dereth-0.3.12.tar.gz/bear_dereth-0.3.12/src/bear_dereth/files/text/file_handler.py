"""Simple text file handler for line-agnostic IO with locking.

This is a minimal, reusable file handler intended for formats like
JSON (full-text) or general text. It provides safe read_text and
write_text operations with file locking and lazy handle management.

Note: For JSONL (line-oriented) use JSONLFilehandler, which provides
specialized iter/line APIs.
"""

from __future__ import annotations

from typing import IO, TYPE_CHECKING, Any, Self

from bear_dereth.files.base_file_handler import BaseFileHandler
from bear_dereth.files.file_lock import FileLock

if TYPE_CHECKING:
    from pathlib import Path


class TextFileHandler(BaseFileHandler[str]):
    """A simple text file handler with locking and lazy open.

    - Lazily opens the file on first use
    - Uses fcntl file locks for read/write sections
    - Provides read_text(), write_text(), clear(), and basic handle helpers
    """

    def __init__(self, file: str | Path, mode: str = "a+", encoding: str = "utf-8") -> None:
        """Initialize the text file handler."""
        super().__init__(file=file, mode=mode, encoding=encoding)

    def read(self, **kwargs) -> str:
        """Read the entire file (or up to n chars) as text with a shared lock."""
        handle: IO[Any] | None = self.handle()
        if handle is None:
            raise ValueError("File handle is not available.")
        with FileLock(handle, exclusive=False):
            handle.seek(0)
            data: str = handle.read(kwargs.pop("n", -1))
            return data

    def write(self, data: str, **kwargs) -> None:
        """Replace file contents with text using an exclusive lock."""
        handle: IO[Any] | None = self.handle()
        if handle is None:
            raise ValueError("File handle is not available.")
        with FileLock(handle, exclusive=True):
            handle.seek(0)
            handle.truncate(0)
            handle.write(data)
            handle.flush()

    def __enter__(self) -> Self:
        """Enter the runtime context related to this object."""
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        """Exit the runtime context and close the file handle."""
        self.close()


# ruff: noqa: ARG002
