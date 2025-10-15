"""A simple logger setup."""

from .consts import FILE_MODE, BaseOutput, CallableOrFile, ExtraStyle, HandlerModes
from .log_level import LevelHandler, LogLevel

__all__ = [
    "FILE_MODE",
    "BaseOutput",
    "CallableOrFile",
    "ExtraStyle",
    "HandlerModes",
    "LevelHandler",
    "LogLevel",
]
