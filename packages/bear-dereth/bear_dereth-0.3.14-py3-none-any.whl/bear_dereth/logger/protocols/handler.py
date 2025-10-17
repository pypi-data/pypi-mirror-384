"""A module defining a protocol for log message handlers."""

from collections.abc import Callable
from typing import IO, Any, ClassVar, Protocol, Self, TextIO

from bear_dereth.logger.common.consts import HandlerModes
from bear_dereth.logger.common.log_level import LogLevel


class Handler[Handler_Type: TextIO | IO](Protocol):
    """A protocol for log message handlers."""

    default_mode_attr: ClassVar[str] = ""
    alt_mode_attr: ClassVar[str] = ""

    name: str | None
    level: LogLevel
    disabled: bool
    mode: HandlerModes
    caller: Any
    file: Handler_Type | None

    def __init__(self, disabled: bool = False) -> None:
        """A constructor for the Handler protocol."""
        self.disabled = disabled
        self.mode = "default"

    def on_init(self, *args: Any, **kwargs: Any) -> None:
        """A hook for additional initialization if needed."""

    @property
    def mode_attr(self) -> str:
        """Get the current mode attribute based on the handler's mode."""
        return self.default_mode_attr if self.mode == "default" else self.alt_mode_attr

    def output_func(self) -> Callable[..., Any]:
        """Get the appropriate output function based on the current mode."""
        get_func: Callable | None = getattr(self.caller, self.mode_attr, None)
        if not get_func or not callable(get_func):
            raise AttributeError(f"Console has no callable attribute '{self.mode_attr}'")
        return get_func

    def emit(self, msg: object, style: str, level: LogLevel, **kwargs) -> None:
        """Emit a log message with the given style and arguments.

        Args:
            msg: The message object to emit
            style: The Rich style/theme name to apply
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments for Rich formatting
        """

    def set_mode(self, mode: HandlerModes) -> None:
        """Set the mode of the handler, either printing as normal or log-style output."""
        self.mode = mode

    def close(self) -> None:
        """Close the handler and clean up any resources."""
        if (
            hasattr(self, "file")
            and self.file
            and hasattr(self.file, "close")
            and not getattr(self.file, "closed", False)
        ):
            self.file.close()

    def flush(self) -> None:
        """Flush any buffered output."""
        if (
            hasattr(self, "file")
            and self.file
            and hasattr(self.file, "flush")
            and not getattr(self.file, "closed", False)
        ):
            self.file.flush()

    def set_level(self, level: str | int | LogLevel) -> None:
        """Set the logging level for this handler."""
        self.level = LogLevel.get(level, default=self.level)

    def should_emit(self, level: LogLevel) -> bool:
        """Check if this handler should emit messages at the given level."""
        return level >= self.level

    def __enter__(self) -> Self:
        """Enter the runtime context related to this object."""
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        """Exit the runtime context related to this object."""
        self.close()
