"""Base file handler protocol and minimal implementation."""

from __future__ import annotations

from abc import abstractmethod
from contextlib import suppress
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any, Protocol, Self

from bear_dereth.files.file_lock import FileLock
from bear_dereth.files.helpers import touch

if TYPE_CHECKING:
    from pydantic import BaseModel


class FileHandlerProtocol[T](Protocol):
    """Basic protocol for file handlers."""

    def read(self, **kwargs) -> T:
        """Return parsed records from the file (format-specific in subclass)."""
        raise NotImplementedError

    def write(self, data: T, **kwargs) -> None:
        """Replace file contents with `data` (format-specific in subclass)."""
        raise NotImplementedError

    def clear(self) -> None:
        """Clear the file contents using an exclusive lock."""
        raise NotImplementedError

    @property
    def closed(self) -> bool:
        """Check if the file handle is closed."""
        raise NotImplementedError

    def close(self) -> None:
        """Close the file handle if open."""
        raise NotImplementedError

    def flush(self) -> None:
        """Flush the file handle if open."""
        raise NotImplementedError


class BaseFileHandler[T](FileHandlerProtocol):
    """Minimal base for file-backed handlers.

    Owns: path/mode/encoding, lazy-open/close, properties, basic IO helpers,
    and lock hooks you can override. Knows nothing about data format.
    """

    def __init__(self, file: str | Path, mode: str = "a+", encoding: str | None = None) -> None:
        """Initialize the base file handler."""
        self.file = Path(file)
        self._mode: str = mode
        self.encoding: str | None = encoding
        self._handle: IO[Any] | None = None

    def _open(self, **kwargs: Any) -> IO[Any]:
        """Default opener. Subclasses can override if needed."""
        touch(self.file, mkdir=True)
        return open(file=self.file, mode=self._mode, encoding=self.encoding, **kwargs)

    def handle(self, open_file: bool = True) -> IO[Any] | None:
        """Get the file handle, opening it if needed."""
        if not open_file:
            return self._handle
        if self._handle is None or self._handle.closed:
            self._handle = self._open()
        return self._handle

    @abstractmethod
    def read(self, **kwargs) -> T:
        """Return parsed records from the file (format-specific in subclass)."""

    @abstractmethod
    def write(self, data: T, **kwargs) -> None:
        """Replace file contents with `data` (format-specific in subclass)."""

    def clear(self) -> None:
        """Clear the file contents using an exclusive lock."""
        handle: IO[Any] | None = self.handle()
        if handle is None:
            raise ValueError("File handle is not available.")
        with FileLock(handle=handle, exclusive=True):
            handle.seek(0)
            handle.truncate(0)

    def flush(self) -> None:
        """Flush the file handle if open."""
        h: IO[Any] | None = self.handle(open_file=False)
        if not h:
            return
        h.flush()

    def seek(self, offset: int, whence: int = 0) -> int:
        """Seek to a specific position in the file."""
        h: IO[Any] | None = self.handle()
        if h is None:
            raise ValueError("File handle is not available.")
        return h.seek(offset, whence)

    def truncate(self, size: int | None = None) -> int:
        """Truncate the file to at most size bytes."""
        h: IO[Any] | None = self.handle()
        if h is None:
            raise ValueError("File handle is not available.")
        return h.truncate(size)

    def tell(self) -> int:
        """Get the current file position."""
        h: IO[Any] | None = self.handle()
        if h is None:
            raise ValueError("File handle is not available.")
        return h.tell()

    def seekable(self) -> bool:
        """Check if the file is seekable."""
        h: IO[Any] | None = self.handle(open_file=False)
        return bool(h and h.seekable())

    def readable(self) -> bool:
        """Check if the file is readable based on mode."""
        return "r" in self._mode or "+" in self._mode

    def writable(self) -> bool:
        """Check if the file is writable based on mode."""
        return any(m in self._mode for m in ("w", "a")) or "+" in self._mode

    def close(self) -> None:
        """Close the file handle if open."""
        if self.closed:
            return
        h: IO[Any] | None = self.handle(open_file=False)
        if h is not None and not h.closed:
            h.close()
        self._handle = None

    @property
    def closed(self) -> bool:
        """Check if the file handle is closed."""
        h: IO[Any] | None = self.handle(open_file=False)
        return not h or h.closed

    @property
    def mode(self) -> str:
        """Get the file mode."""
        h: IO[Any] | None = self.handle(open_file=False)
        return h.mode if h else self._mode

    @property
    def name(self) -> str:
        """Get the file name."""
        h: IO[Any] | None = self.handle(open_file=False)
        return h.name if h else str(self.file)

    def from_pydantic(self, model: BaseModel, exclude_none: bool = False, **kwargs) -> T:
        """Convert Pydantic model to YAML-compatible dictionary.

        Args:
            model: Pydantic model instance
            exclude_none: Exclude None values from output
            **kwargs: Additional model_dump arguments

        Returns:
            Dictionary representation suitable for YAML serialization
        """
        return model.model_dump(mode="json", exclude_none=exclude_none, **kwargs)  # type: ignore[return-value]

    def to_pydantic(self, model_class: type[BaseModel]) -> BaseModel:
        """Convert YAML data to Pydantic model.

        Args:
            model_class: Pydantic model class to create

        Returns:
            Validated Pydantic model instance

        Raises:
            ValueError: If data cannot be converted
        """
        data: T = self.read()
        try:
            return model_class.model_validate(data)
        except Exception as e:
            raise ValueError(f"Cannot convert data to {model_class.__name__}: {e}") from e

    def __enter__(self) -> Self:
        if self.closed:
            self.handle(open_file=True)
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def __del__(self) -> None:
        with suppress(Exception):
            self.close()
