"""This module provides textio-like classes for various purposes, including a mock TextIO for testing."""

from collections.abc import Callable, Iterable, Iterator
import sys
from types import SimpleNamespace as Namespace
from typing import IO, Any, Self, TextIO

from singleton_base import SingletonWrap


class MockTextIO(TextIO):
    """A mock TextIO class that captures written output for testing purposes."""

    def __init__(self) -> None:
        """Initialize the mock TextIO."""
        self._buffer: list[str] = []
        self._counters: Namespace = Namespace()
        self.num_init = 1

    def __getattr__(self, name: str):
        if name.startswith("num_") and hasattr(self._counters, name):
            return getattr(self._counters, name)
        raise AttributeError(f"{self.__class__.__name__} has no attribute {name}")

    def __setattr__(self, attr_name: str, value: int) -> None:
        if attr_name.startswith("num_"):
            if not hasattr(self._counters, attr_name):
                setattr(self._counters, attr_name, 0)
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"Counter {attr_name} must be a non-negative integer")
            setattr(self._counters, attr_name, value)
        else:
            super().__setattr__(attr_name, value)

    def write(self, s: Any) -> int:
        """Mock write method that appends to the buffer."""
        self._buffer.append(s)
        self.num_write += 1
        return self.num_write

    def read(self, n: int = -1) -> str:
        """Mock read method that returns an empty string."""
        self.num_read += 1
        return ""

    def output_buffer(self) -> list[str]:
        """Get the output buffer."""
        self.num_output_buffer += 1
        return self._buffer

    def clear(self) -> None:
        """Clear the output buffer."""
        self.num_clear += 1
        self._buffer.clear()

    def flush(self) -> None:
        """Mock flush method that does nothing."""
        self.num_flush += 1

    def close(self) -> None:
        """Mock close method that does nothing."""
        self.num_close += 1


class NullFile(TextIO, IO[str]):
    """A null file that discards all writes, implementing the singleton pattern.

    It does this to ensure there is only one instance of NullFile throughout the application since
    there is no need for multiple instances of a null file.
    """

    def flush(self) -> None: ...
    def writelines(self, __lines: Iterable[str]) -> None: ...
    def close(self) -> None: ...
    def isatty(self) -> bool:
        return False

    def closed(self) -> bool:  # type: ignore[override]
        return True

    def read(self, __n: int = 1) -> str:
        return ""

    def readable(self) -> bool:
        return False

    def readline(self, __limit: int = 1) -> str:
        return ""

    def readlines(self, __hint: int = 1) -> list[str]:
        return []

    def seek(self, __offset: int, __whence: int = 1) -> int:
        return 0

    def seekable(self) -> bool:
        return False

    def tell(self) -> int:
        return 0

    def truncate(self, __size: int | None = 1) -> int:
        return 0

    def writable(self) -> bool:
        return False

    def __next__(self) -> str:
        return ""

    def __iter__(self) -> Iterator[str]:
        return iter([""])

    def __enter__(self) -> Self:
        return self

    def __exit__(self, _: object, __: object, ___: object) -> None:
        """Nothing to clean up."""

    def write(self, text: str) -> int:
        return 0

    def fileno(self) -> int:
        return -1


def stdout() -> TextIO:
    """Get current stdout, respecting any redirects."""
    return sys.stdout


def stderr() -> TextIO:
    """Get current stderr, respecting any redirects."""
    return sys.stderr


NullCls: SingletonWrap[NullFile] = SingletonWrap(NullFile)


def null_file() -> TextIO:
    """Get a null file that discards all writes."""
    return NullCls.get()


STDOUT: Callable[[], TextIO] = stdout
"""Callable that returns the current stdout"""
STDERR: Callable[[], TextIO] = stderr
"""Callable that returns the current stderr"""
DEVNULL: Callable[[], TextIO] = null_file
"""A null file callable that discards all writes."""
NULL_FILE: TextIO = null_file()
"""A singleton instance of NullFile that discards all writes."""


__all__ = [
    "DEVNULL",
    "STDERR",
    "STDOUT",
    "MockTextIO",
    "NullFile",
    "stderr",
    "stdout",
]

# ruff: noqa: D102 PYI063 ARG002
