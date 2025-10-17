"""This module provides the BearLogger class for printing messages using the Rich library with a handler-based architecture."""

from __future__ import annotations

from functools import partial
from io import StringIO
from typing import IO, TYPE_CHECKING, Any, Self, TextIO, cast

from rich import inspect as rich_inspect
from rich.console import Console

from bear_dereth.di import Provide, inject
from bear_dereth.files.textio_utility import NULL_FILE, stderr, stdout
from bear_dereth.logger.common.log_level import LogLevel
from bear_dereth.logger.core.config import ConsoleOptions, Container, CustomTheme, LoggerConfig, get_container
from bear_dereth.logger.handlers.console_handler import ConsoleHandler
from bear_dereth.logger.protocols.printer import LoggerPrinter

if TYPE_CHECKING:
    from rich.status import Status

    from bear_dereth.logger.protocols.handler import Handler
    from bear_dereth.logger.simple_logger import SimpleLogger


class BearLogger[T: TextIO | IO](LoggerPrinter):
    """A Rich-powered logger with handler-based architecture for the bear ecosystem."""

    @inject
    def __init__(
        self,
        name: str | None = None,
        level: str | int | LogLevel = LogLevel.DEBUG,
        config: LoggerConfig = Provide[Container.config],
        console_options: ConsoleOptions = Provide[Container.console_options],
        custom_theme: CustomTheme = Provide[Container.custom_theme],
        error_logger: SimpleLogger | None = None,
        root_level: LogLevel = Provide[Container.root_level],
        handlers: list[Handler[Any]] | None = None,
        **kwargs,
    ) -> None:
        """Initialize the BearLogger with handler-based architecture.

        Theme is derived from the default configuration, either in ~/.config/bear_dereth/logger/default.yaml or
        <project_root>/config/bear_dereth/logger/default.yaml or it can be overridden by passing a CustomTheme instance.

        Args:
            name: Optional name for the logger
            config: Logger configuration. If None, uses default config.
            custom_theme: A custom theme to use. If None, derived from config.
            level: Logging level for this logger.
            **kwargs: Additional keyword arguments to pass to the default Console handler.
        """
        self.name = name
        self.config = config
        self.level = LogLevel.get(level, default=root_level)
        super().__init__(
            name=self.name,
            config=self.config,
            level=self.level,
            error_logger=error_logger,
        )
        console_options = console_options.model_copy(update=self.config.root.overrides)
        self.console_options: ConsoleOptions = console_options.model_copy(update=kwargs)
        self.theme: CustomTheme = custom_theme

        self.handlers: list[Handler[Any]] = handlers or []
        self._file = NULL_FILE
        self.on_init()
        self._setup_dynamic_methods()

    def on_init(self) -> None:
        """Hook for additional initialization if needed."""
        container: Container = get_container()
        container.register("error_callback", self.on_error_callback)
        container.register("root_level", self.get_level)

        self._console = Console(**self.console_options.model_dump(exclude_none=True))
        self._file = cast("TextIO | IO", self._console.file)
        self._buffer = StringIO()
        if not self.handlers:
            self.console_handler: ConsoleHandler[TextIO] = ConsoleHandler()
            self.add_handler(self.console_handler)

    def _setup_dynamic_methods(self) -> None:
        for style in self.config.theme.model_dump():
            setattr(self, style, partial(self._wrapped_print, style=style, level=style.upper()))

    def _wrapped_print(self, msg: object, style: str, level: str, **kwargs) -> None:
        """Print a message with a specific style via handlers."""
        try:
            exc_info: bool = kwargs.pop("exc_info", style == "exception")
            if exc_info:
                self._emit_to_handlers(msg=self.print_exception(**kwargs), level=LogLevel.ERROR, style=style, **kwargs)
            lvl: LogLevel = LogLevel.get(level, default=LogLevel.INFO)
            self._emit_to_handlers(msg=msg, level=lvl, style=style, **kwargs)
        except Exception as e:
            self.on_error_callback("There was issue using one of the named methods", name=style, error=e)

    def _emit_to_handlers(self, msg: object, level: LogLevel, style: str, **kwargs) -> None:
        """Emit a message to all handlers with error handling."""
        if level < self.level:
            return
        for handler in self.handlers:
            try:
                handler.emit(msg=msg, style=style, level=level, **kwargs)
            except Exception as e:
                self.on_error_callback("Error during _emit_to_handlers step", name=handler.name or "handler", error=e)

    def print_exception(self, **kwargs) -> str:
        """Print an exception using the console's print_exception method."""
        og_file: IO[str] = self._console.file
        self._console.file = self._buffer
        self._console.print_exception(show_locals=True, **kwargs)
        self._console.file = og_file
        exception_text: str = self._buffer.getvalue()
        self._buffer.truncate(0)
        self._buffer.seek(0)
        return exception_text

    @property
    def file(self) -> T:
        """Get the current file object from the main console."""
        file = self._file or (stderr() if self._console.stderr else stdout())
        file = getattr(file, "rich_proxied_file", file)
        if file is None:
            file = NULL_FILE
        return cast("T", file)

    @file.setter
    def file(self, new_file: T) -> None:
        """Set a new file object for the main console."""
        self._file = new_file
        self._console.file = new_file

    def print(self, msg: object, style: str | None = None, **kwargs) -> None:
        """Print a message with a specific style directly to the console."""
        exc_info: bool = kwargs.pop("exc_info", style == "exception")
        if exc_info:
            self._console.print_exception(show_locals=True)
        self._console.print(msg, style=style, **kwargs)

    def print_json(self, json: str | None = None, data: Any = None, **kwargs) -> None:
        """Print a JSON object with rich formatting."""
        self._console.print_json(json=json, data=data, **kwargs)

    def inspect(self, obj: object, **kwargs) -> None:
        """Inspect an object and print its details."""
        rich_inspect(obj=obj, console=self._console, **kwargs)

    def log(self, *msg: object, **kwargs) -> None:
        """Log a message to the console."""
        self._console.log(*msg, **kwargs)

    def status(self, status: str, **kwargs) -> Status:
        """Create a status context manager for displaying a status message."""
        return self._console.status(status=status, **kwargs)

    def close(self) -> None:
        """Close all handlers and clean up resources."""
        for handler in self.handlers:
            try:
                handler.close()
            except Exception as e:
                self.on_error_callback("Error during handler close", name=handler.name or "handler", error=e)

    def flush(self) -> None:
        """Flush all handlers."""
        for handler in self.handlers:
            try:
                handler.flush()
            except Exception as e:
                self.on_error_callback("Error during handler flush", name=handler.name or "handler", error=e)

    def __enter__(self) -> Self:
        """Enter the runtime context related to this object."""
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        """Exit the runtime context related to this object."""
        self.close()
