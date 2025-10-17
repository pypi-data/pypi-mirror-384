"""Template-based formatter using string.Template for log messages."""

from __future__ import annotations

from string import Template
import traceback
from typing import TYPE_CHECKING, Any

from bear_epoch_time import EpochTimestamp
from bear_epoch_time.constants import PT_TIME_ZONE

from bear_dereth.logger.core.config import FormatterConfig
from bear_dereth.logger.protocols import Formatter

if TYPE_CHECKING:
    from datetime import datetime

    from bear_dereth.logger.common._stack_info import StackInfo
    from bear_dereth.logger.common.log_level import LogLevel


class TemplateFormatter(Formatter):
    """A formatter that uses string.Template for flexible log formatting.

    Uses $variable syntax for template substitution, making it easy to create
    readable format strings without worrying about brace escaping.
    """

    def __init__(
        self,
        name: str | None = None,
        fmt: str | None = None,
        exception_fmt: str | None = None,
        config: FormatterConfig | None = None,
    ) -> None:
        """Initialize the template formatter.

        Args:
            name: Optional name for the formatter
            fmt: Format template string (falls back to config.console_fmt)
            exception_fmt: Exception template string (falls back to config.exception_fmt)
            config: Formatter configuration (uses defaults if not provided)
        """
        self.name: str | None = name
        self.config: FormatterConfig = config or FormatterConfig()

        self.fmt: str = fmt or self.config.console_fmt
        self.exception_fmt: str = exception_fmt or self.config.exception_fmt or self.fmt

        self._template = Template(self.fmt)
        self._exception_template = Template(self.exception_fmt)

    def format(
        self,
        message: object,
        level: LogLevel,
        stack_info: StackInfo,
        timestamp: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Format a log message using the configured template.

        Args:
            message: The log message object to format
            level: The log level for this message
            stack_info: Information about where the log was called from
            timestamp: Optional timestamp string (generated if not provided)
            **kwargs: Additional context data for formatting

        Returns:
            A formatted string ready for output by a handler
        """
        if timestamp is None:
            timestamp = self._format_timestamp()

        substitutions: dict[str, Any] = stack_info.model_dump(exclude_none=True)
        substitutions.update(
            {
                "timestamp": timestamp,
                "level": level.name,
                "level_value": level.value,
                "message": str(message),
                **kwargs,  # Allow additional context
            }
        )
        return self._template.safe_substitute(**substitutions)

    def format_exception(
        self,
        message: object,
        level: LogLevel,
        stack_info: StackInfo,
        exception: Exception,
        timestamp: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Format an exception log message using the exception template.

        Args:
            message: The log message object to format
            level: The log level for this message
            stack_info: Information about where the log was called from
            exception: The exception that occurred
            timestamp: Optional timestamp string (generated if not provided)
            **kwargs: Additional context data for formatting

        Returns:
            A formatted string with exception details ready for output
        """
        if timestamp is None:
            timestamp = self._format_timestamp()

        exception_details: str = self._format_exception_details(exception)

        substitutions = stack_info.model_dump(exclude_none=True)
        # TODO: We should reuse the data data structure here

        substitutions: dict[str, Any] = {
            "timestamp": timestamp,
            "level": level.name,
            "level_value": level.value,
            "message": str(message),
            "filename": stack_info.filename.name,
            "filepath": str(stack_info.filename),
            "caller_function": stack_info.caller_function,
            "line_number": stack_info.line_number,
            "exception": str(exception),
            "exception_class": type(exception).__name__,
            "exception_details": exception_details,
            **kwargs,  # Allow additional context
        }
        return self._exception_template.safe_substitute(**substitutions)

    def _handle_iso_format(self, now: EpochTimestamp) -> str:
        # TODO: This should be a config setting here, I'm using use my local timezone for now
        dt: datetime = now.to_datetime.astimezone(tz=PT_TIME_ZONE)
        if self.config.include_microseconds:
            return dt.isoformat()
        return dt.isoformat(timespec="seconds")

    def _format_timestamp(self) -> str:
        """Generate a formatted timestamp string."""
        now: EpochTimestamp = EpochTimestamp.now()

        if self.config.iso_format:
            return self._handle_iso_format(now)

        fmt: str = self.config.datefmt
        if self.config.include_microseconds and "%f" not in fmt:
            fmt = fmt + ".%f"
        return now.to_string(fmt=fmt)

    def _format_exception_details(self, exception: Exception) -> str:
        """Format exception details including stack trace if enabled."""
        if not self.config.include_stack_trace:
            return f"{type(exception).__name__}: {exception}"

        exception_lines: list[str] = traceback.format_exception(type(exception), exception, exception.__traceback__)
        full_trace: str = "".join(exception_lines)

        if len(full_trace) > self.config.max_exception_length:
            truncated: str = full_trace[: self.config.max_exception_length]
            return f"{truncated}\n... (truncated at {self.config.max_exception_length} chars)"

        return full_trace.rstrip()

    def __repr__(self) -> str:
        """String representation of the formatter."""
        return f"TemplateFormatter(name={self.name!r}, fmt={self.fmt!r})"


if __name__ == "__main__":
    now: EpochTimestamp = EpochTimestamp.now()
    print(now.to_string())
    dt: datetime = now.to_datetime.astimezone(tz=PT_TIME_ZONE)
    print(dt)
