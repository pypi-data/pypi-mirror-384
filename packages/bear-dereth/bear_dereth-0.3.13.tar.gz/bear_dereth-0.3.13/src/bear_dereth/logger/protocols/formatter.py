"""Formatter protocol definition for the logger system."""

from typing import Any, Protocol

from bear_dereth.logger.common._stack_info import StackInfo
from bear_dereth.logger.common.log_level import LogLevel


class Formatter(Protocol):
    """A protocol for log message formatters.

    Formatters are responsible for transforming raw log data into formatted strings
    that can be consumed by handlers for output.
    """

    name: str | None

    def __init__(self, name: str | None = None, fmt: str | None = None, exec_fmt: str | None = None) -> None:
        """Initialize the formatter with an optional name and format templates.

        Args:
            name: Optional name for the formatter
            exec_fmt: Optional separate template for exception messages (falls back to fmt if not provided)
        """
        ...

    def format(
        self,
        message: object,
        level: LogLevel,
        stack_info: StackInfo,
        timestamp: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Format a log message into a string.

        Args:
            message: The log message object to format
            level: The log level for this message
            stack_info: Information about where the log was called from
            timestamp: Optional timestamp string
            **kwargs: Additional context data for formatting

        Returns:
            A formatted string ready for output by a handler
        """
        ...

    def format_exception(
        self,
        message: object,
        level: LogLevel,
        stack_info: StackInfo,
        exception: Exception,
        timestamp: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Format an exception log message into a string.

        Args:
            message: The log message object to format
            level: The log level for this message
            stack_info: Information about where the log was called from
            exception: The exception that occurred
            timestamp: Optional timestamp string
            **kwargs: Additional context data for formatting

        Returns:
            A formatted string with exception details ready for output
        """
        ...
