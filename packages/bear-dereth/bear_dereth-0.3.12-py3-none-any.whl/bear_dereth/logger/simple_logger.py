"""Simple logger implementation with log levels and timestamped output."""

from collections.abc import Callable, Collection, Mapping
from functools import cached_property
from inspect import isclass
import traceback
from typing import Any, Literal

from bear_epoch_time import DT_FORMAT_WITH_SECONDS, PT_TIME_ZONE, TIME_FORMAT_WITH_SECONDS
from bear_epoch_time.tz import TimeZoneType
from rich.console import Console

from bear_dereth.dynamic_meth import dynamic_methods
from bear_dereth.files.textio_utility import stderr
from bear_dereth.logger.common._file_mode import get_file_mode
from bear_dereth.logger.common._time import TimeHelper
from bear_dereth.logger.common.consts import (
    METHOD_NAMES,
    WITHOUT_EXCEPTION_NAMES,
    BaseOutput,
    CallableOrFile,
    ExtraStyle,
)
from bear_dereth.logger.common.log_level import LogLevel
from bear_dereth.logger.protocols.logger_type import TypeLogger
from bear_dereth.stringing.flatten_data import ArrayLike, flatten
from bear_dereth.typing_tools import TypeHint


class PrintWrapper:
    def output(self, *args: object, **kwargs: Any) -> None:
        print(*args, **kwargs)


WriteMode = Literal["print", "buffer"]


class BaseLogger[Callable_T]:
    """A simple logger that writes messages to stdout, stderr, or StringIO with a timestamp."""

    def __init__(
        self,
        name: str = "logger",
        level: LogLevel | int | str = LogLevel.DEBUG,
        *,
        file: CallableOrFile | None = None,
        file_callback: CallableOrFile | None = stderr,
        file_mode: BaseOutput | None = None,
        caller: type[Callable_T] = PrintWrapper,
        caller_attr: str = "output",
        sep: str = " ",
        end: str = "\n",
        flush: bool = False,
        extra_style: ExtraStyle = "flatten",
        write_mode: WriteMode = "print",
        date_time_fmt: str = DT_FORMAT_WITH_SECONDS,
        time_format: str = TIME_FORMAT_WITH_SECONDS,
        time_zone: TimeZoneType = PT_TIME_ZONE,
        **kwargs,
    ) -> None:
        """Initialize the ErrorLogger.

        Args:
            name: The name of the logger.
            level: The logging level for this logger.
            file: A specific TextIO or IO object to use, overrides file_callback and file_mode.
            file_callback: A callable that returns a TextIO or IO object, overrides file_mode.
            file_mode: A string representing the desired file mode, one of 'stdout', 'stderr', 'devnull', or 'string_io'.
            caller: A callable or class that has a method to output the log messages.
            caller_attr: The attribute name of the method in the caller to use for output.
            sep: Separator between values. Defaults to a single space.
            end: String appended after the last value. Defaults to a newline.
            flush: Whether to forcibly flush the stream. Defaults to False.
            extra_style: How to handle extra keyword arguments - 'flatten' or 'no_flatten'.
            write_mode: How to handle writing messages - 'print' to output immediately, 'buffer' to store in an internal buffer.
            time_format: The format string for timestamps.
            time_zone: The timezone to use for timestamps.
            **kwargs: Additional keyword arguments, for now, they are only stored but not used.
        """
        self.name: str = name
        self.level: LogLevel = LogLevel.get(level, default=LogLevel.DEBUG)
        self._file: CallableOrFile = get_file_mode(mode=file_mode, callback=file_callback, file=file)
        self._caller: Callable_T = caller() if isclass(caller) else caller
        self._caller_attr: str = caller_attr
        self.sep: str = sep
        self.end: str = end
        self.flush: bool = flush
        self.extra_style: ExtraStyle = extra_style
        self.write_mode: WriteMode = write_mode
        self.date_time_fmt: str = date_time_fmt
        self.time_format: str = time_format
        self.time_zone: TimeZoneType = time_zone
        self.time = TimeHelper(fmt=date_time_fmt, time_fmt=time_format, tz=time_zone)
        self.buffer: list[str] = []
        self.kwargs: dict[str, Any] = kwargs

    def write(self, msg: str) -> None:
        """Write a message directly to the caller's output method."""
        match self.write_mode:
            case "print":
                self(msg, end=self.end, sep=self.sep, file=self.file, flush=self.flush)
            case "buffer":
                self.buffer.append(msg)
            case _:
                raise ValueError(f"Invalid write_mode: {self.write_mode}")

    def read(self, clear: bool = False) -> str:
        """Read the current contents of the internal buffer as a single string."""
        output: str = self.end.join(self.buffer)
        if clear:
            self.clear()
        return output

    def clear(self) -> None:
        """Clear the internal buffer."""
        self.buffer.clear()

    def should_log(self, level: LogLevel) -> bool:
        """Determine if a message at the given level should be logged.

        Args:
            level: The LogLevel to check against the current logger's level.

        Returns:
            True if the message should be logged, False otherwise.
        """
        return level >= self.level

    def timestamp(self) -> str:
        """Get the current time formatted according to the instance's time_format."""
        return self.time.get_current_time()

    def format(self, prefix: str = "", data: Mapping | Collection | None = None) -> str:
        """Format keyword arguments into a string.

        Args:
            **kwargs: Keyword arguments to format.

        Returns:
            A formatted string of key=value pairs.
        """
        if self.extra_style == "flatten" and data is not None:
            return flatten(data, prefix).get(combine=True)
        if isinstance(data, Collection) and not isinstance(data, Mapping):
            return " ".join(f"{prefix}{i}={value}" for i, value in enumerate(data))
        if isinstance(data, Mapping):
            return " ".join(f"{prefix}{key}={value}" for key, value in data.items())
        return ""

    def flatten_data(self, values: ArrayLike | Mapping, prefix: str = "") -> str:
        """Flatten nested data structures into a single string.

        This includes dictionaries, lists, tuples, and sets.

        Args:
            values: A dictionary or list of values to flatten.
            prefix: An optional prefix to prepend to each flattened value.

        Returns:
            A single flattened string with values separated by the instance's sep.
        """
        return flatten(values, prefix).get(combine=True)

    def to_log(self, level: LogLevel, *args: object, **kwargs) -> None:
        """A method to log a message via console.log()."""
        if self.should_log(level):
            self(*args, **kwargs)

    @cached_property
    def caller(self) -> Callable[..., None]:
        """Get the current caller instance."""
        caller: Callable_T = self._caller
        if isclass(self._caller):
            caller: Callable_T = self._caller()
        if not hasattr(caller, self._caller_attr):
            raise AttributeError(f"The caller does not have the attribute '{self._caller_attr}'")
        return getattr(caller, self._caller_attr)

    @property
    def file(self) -> CallableOrFile:
        """Get the current output file."""
        return self._file() if callable(self._file) else self._file or stderr()

    @file.setter
    def file(self, file_callback: CallableOrFile) -> None:
        """Set the output file callback."""
        self._file = file_callback() if callable(file_callback) else file_callback

    def __call__(
        self,
        *values: object,
        sep: str | None = None,
        end: str | None = None,
        flush: bool | None = None,
        file: CallableOrFile | None = None,
        **kwargs,
    ) -> None:
        """Print the error message to the specified file with optional formatting.

        Args:
            *values: Values to be printed.
            level: The LogLevel for this message. Defaults to LogLevel.DEBUG.
            sep: Separator between values. Defaults to the instance's sep.
            end: String appended after the last value. Defaults to the instance's end.
            flush: Whether to forcibly flush the stream. Defaults to the instance's flush.
            file: The file to write to. Defaults to the instance's file.
            **kwargs: Additional keyword arguments to pass to the print function, that will be formatted as key=value pairs
                or flattened if flatten is True.
        """
        sep = sep if sep is not None else self.sep
        end = end if end is not None else self.end
        flush = flush if flush is not None else self.flush
        file = file if file is not None else self.file
        kwargs_str: str = self.format(prefix="kwargs.", data=kwargs) if kwargs else ""
        self.caller(*(*values, kwargs_str) if kwargs_str else values, end=end, sep=sep, file=file, flush=flush)


@dynamic_methods(methods=METHOD_NAMES, delegate_to="log")
class PrintOnlyLogger(BaseLogger, TypeHint(TypeLogger)):
    """The simplest logger implementation - prints to console only.

    Setup to use log levels, but does not store or process messages in any way.
    """

    def log(self, msg: object, sep: str = " ", end: str = "\n", **kwargs) -> None:
        """Log a message at the specified level"""
        level: LogLevel = kwargs.pop("level", LogLevel.INFO)
        self.to_log(level, msg, sep=sep, end=end, **kwargs)


@dynamic_methods(WITHOUT_EXCEPTION_NAMES, delegate_to="log")
class SimpleLogger[Caller_T](BaseLogger[Caller_T], TypeHint(TypeLogger)):
    """A simple logger that writes messages to stdout, stderr, or StringIO with a timestamp."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """A constructor for the SimpleLogger protocol."""
        super().__init__(*args, write_mode="buffer", **kwargs)

    def print(self, msg: object, end: str = "\n", sep: str = " ") -> None:
        """Print the message to the specified file with an optional end character."""
        self(msg, end=end, sep=sep, file=self.file, flush=self.flush, **self.kwargs)

    def log(self, msg: object, *args, **kwargs) -> None:
        """Log a message at the specified level."""
        level: LogLevel = kwargs.pop("level", LogLevel.INFO)
        if not self.should_log(level):
            return
        self.write(f"[{self.timestamp()}] [{level.text}]: {msg}")
        self.write(flatten(args, "args").get(combine=True)) if args else None
        self.write(flatten(kwargs, "kwargs").get(combine=True)) if kwargs else None
        self.print(self.read(clear=True))

    def exception(self, msg: object, *args, **kwargs) -> None:
        """Log an exception message with optional exception info."""
        self.log(
            LogLevel.EXCEPTION,
            msg,
            *args,
            exc_info=traceback.format_exc(),
            **kwargs,
        )


class ConsoleSimple(SimpleLogger[Console]): ...


__all__ = ["BaseLogger", "PrintOnlyLogger", "SimpleLogger"]

if __name__ == "__main__":
    printer = PrintOnlyLogger(name="printer", level=LogLevel.DEBUG)
    printer.debug("This is a debug message.")
