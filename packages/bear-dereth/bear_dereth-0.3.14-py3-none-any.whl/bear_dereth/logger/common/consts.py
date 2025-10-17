"""A collection of common constants for the logging system."""

from collections.abc import Callable
from io import StringIO
from typing import IO, Literal, TextIO

from bear_dereth.files.textio_utility import DEVNULL, stderr, stdout
from bear_dereth.logger.common.log_level import LogLevel

METHOD_NAMES: dict[str, dict[str, LogLevel]] = {
    "debug": {"level": LogLevel.DEBUG},
    "info": {"level": LogLevel.INFO},
    "warning": {"level": LogLevel.WARNING},
    "error": {"level": LogLevel.ERROR},
    "exception": {"level": LogLevel.EXCEPTION},
    "verbose": {"level": LogLevel.VERBOSE},
    "success": {"level": LogLevel.SUCCESS},
    "failure": {"level": LogLevel.FAILURE},
}

HandlerModes = Literal["default", "alt"]
BaseOutput = Literal["stdout", "stderr", "devnull", "string_io"]
ExtraStyle = Literal["flatten", "no_flatten"]
CallableOrFile = Callable[[], TextIO | IO[str] | StringIO] | TextIO | IO[str] | StringIO

WITHOUT_EXCEPTION_NAMES: dict[str, dict[str, LogLevel]] = METHOD_NAMES.copy()
WITHOUT_EXCEPTION_NAMES.pop("exception")

FILE_MODE: dict[BaseOutput, Callable[[], TextIO | IO[str] | StringIO]] = {
    "stdout": stdout,
    "stderr": stderr,
    "devnull": DEVNULL,
    "string_io": StringIO,
}

__all__ = [
    "FILE_MODE",
    "METHOD_NAMES",
    "WITHOUT_EXCEPTION_NAMES",
    "BaseOutput",
    "CallableOrFile",
    "ExtraStyle",
    "HandlerModes",
]
