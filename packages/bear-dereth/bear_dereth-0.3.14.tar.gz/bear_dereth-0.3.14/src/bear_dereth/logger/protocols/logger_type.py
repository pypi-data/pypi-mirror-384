"""A module for defining the TypeLogger protocol."""

from __future__ import annotations

from typing import Protocol


class TypeLogger(Protocol):
    """A way to tell the type checker about logger methods existing but we dynamically add them at runtime."""

    def info(self, msg: object, **kwargs) -> None:
        """Log an info message."""

    def debug(self, msg: object, **kwargs) -> None:
        """Log a debug message."""

    def warning(self, msg: object, **kwargs) -> None:
        """Log a warning message."""

    def error(self, msg: object, **kwargs) -> None:
        """Log an error message."""

    def exception(self, msg: object, **kwargs) -> None:
        """Log an exception message."""

    def verbose(self, msg: object, **kwargs) -> None:
        """Log a verbose message."""

    def success(self, msg: object, **kwargs) -> None:
        """Log a success message."""

    def failure(self, msg: object, **kwargs) -> None:
        """Log a failure message."""


__all__ = ["TypeLogger"]
