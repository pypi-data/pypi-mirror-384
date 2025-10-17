"""A buffer handler for logging output."""

from __future__ import annotations

from io import StringIO
from typing import IO, TYPE_CHECKING, Any, ClassVar, TextIO

from rich.console import Console

from bear_dereth.di import Provide, inject
from bear_dereth.logger.common.log_level import LogLevel
from bear_dereth.logger.core.config import ConsoleOptions, Container
from bear_dereth.logger.protocols.handler import Handler, HandlerModes

if TYPE_CHECKING:
    from collections.abc import Callable

    from bear_dereth.di import Provider


class BufferHandler[Handler_Type: TextIO | IO | StringIO](Handler):
    """A buffer handler that outputs messages to a buffer."""

    default_mode_attr: ClassVar[str] = "print"
    alt_mode_attr: ClassVar[str] = "log"

    @inject
    def __init__(
        self,
        *,
        name: str = "console",
        error_callback: Callable[..., Any] = Provide[Container.error_callback],
        root_level: Callable[[], LogLevel] = Provide[Container.root_level],
        console_options: ConsoleOptions = Provide[Container.console_options],
        file: Handler_Type | None = None,
        level: LogLevel | str | int = LogLevel.DEBUG,
        caller: Console | None = None,
    ) -> None:
        """A constructor for the Handler protocol."""
        self.get_level: Callable[..., LogLevel] = root_level
        self.level = LogLevel.get(level, default=self.get_level())

        super().__init__()
        self.name = name
        self.file = file or StringIO()
        self.error_callback: Callable[..., Any] = error_callback

        self.mode: HandlerModes = "default"
        self.console_options: ConsoleOptions | Provider = console_options
        self.caller: Console = caller or Console(**console_options.model_dump(exclude_none=True))

    def emit(self, msg: object, style: str, level: LogLevel, **kwargs) -> None:
        """Emit a log message with the given style and arguments.

        Args:
            msg: The message object to emit
            style: The Rich style/theme name to apply
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments for Rich formatting
        """
        if self.caller and self.should_emit(level):
            try:
                self.output_func()(msg, style=style, **kwargs)
            except Exception as e:
                self.error_callback("Error during ConsoleHandler emit", error=e, name=self.name or "console_handler")

    def flush(self) -> None:
        """Flush the buffer if it's a StringIO."""
        if isinstance(self.file, StringIO):
            self.file.flush()

    def close(self) -> None:
        """Do nothing with console handler close."""
        if self.file is None:
            return
