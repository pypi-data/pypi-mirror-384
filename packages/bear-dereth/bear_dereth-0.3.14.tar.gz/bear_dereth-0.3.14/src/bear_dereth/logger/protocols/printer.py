"""BasePrinter protocol definition."""

from typing import IO, Any, TextIO

from bear_dereth.logger.common._stack_info import StackInfo
from bear_dereth.logger.common.log_level import LogLevel
from bear_dereth.logger.core.config import CustomTheme, LoggerConfig
from bear_dereth.logger.protocols import BaseHandlerManager, Handler, TypeLogger
from bear_dereth.logger.simple_logger import SimpleLogger
from bear_dereth.typing_tools import TypeHint


class BasePrinter[T: TextIO | IO](BaseHandlerManager):
    """A protocol for a base printer with config, theme, and user API."""

    name: str | None
    config: LoggerConfig
    level: LogLevel
    theme: CustomTheme
    handlers: list[Handler[Any]]
    err: SimpleLogger  # Backup logger for error handling if the main logger fails
    start_no_handlers: bool

    def __init__(
        self,
        name: str | None = None,
        config: LoggerConfig | None = None,
        custom_theme: CustomTheme | None = None,  # noqa: ARG002
        file: T | None = None,  # noqa: ARG002
        level: int | str | LogLevel = LogLevel.DEBUG,
        error_logger: SimpleLogger | None = None,
        start_no_handlers: bool = False,
    ) -> None:
        """A constructor for the BasePrinter protocol."""
        self.name = name
        self.config = config or LoggerConfig()
        self.level = LogLevel.get(level, default=LogLevel.DEBUG)
        self.err = error_logger or SimpleLogger()
        self.start_no_handlers = start_no_handlers

    def get_level(self) -> LogLevel:
        """Get the current logging level."""
        return self.level

    def set_level(self, level: str | int | LogLevel) -> None:
        """Set the current logging level."""
        self.level = LogLevel.get(level, self.level)

    def on_error_callback(self, *msg, name: str, error: Exception) -> None:
        """Handle errors from handlers. Override to customize error handling."""
        stack: StackInfo = StackInfo.from_current_stack()
        code_context: str = (
            stack.code_context[stack.index] if stack.code_context and stack.index is not None else "<unknown>"
        )

        self.err(
            *msg,
            related_name=name,
            caller_function=stack.caller_function,
            code_context=code_context.strip(),
            filename=stack.filename,
            line_number=stack.line_number,
            error_class=type(error).__name__,
            error_text=f"'{error!s}'",
            stack_value=stack.stack_value,
        )

    def print(self, msg: object, style: str | None = None, **kwargs) -> None:
        """A method to print a message with a specific style directly to the console."""

    def log(self, msg: object, *args, **kwargs) -> None:
        """A method to log a message via console.log()."""


class LoggerPrinter(BasePrinter, TypeHint(TypeLogger)):
    """A combined protocol for a logger printer with TypeLogger and BasePrinter features."""
