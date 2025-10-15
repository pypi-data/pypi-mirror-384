"""Override of Rich's Console to add logging methods."""

from collections.abc import Callable, Mapping
from datetime import datetime
import sys
import threading
from time import monotonic
from typing import IO, TYPE_CHECKING, Literal, TextIO, cast

from rich._log_render import FormatTimeCallable, LogRender
from rich._null_file import NULL_FILE
from rich.console import (
    COLOR_SYSTEMS,
    Console,
    ConsoleThreadLocals,
    RenderHook,
    _is_jupyter,  # type: ignore[import]
    detect_legacy_windows,
)
from rich.emoji import EmojiVariant
from rich.highlighter import NullHighlighter, ReprHighlighter
from rich.style import Style, StyleType
from rich.text import Text
from rich.theme import Theme, ThemeStack
from rich.themes import DEFAULT

from bear_dereth.dynamic_meth import dynamic_methods
from bear_dereth.logger.common.consts import METHOD_NAMES
from bear_dereth.logger.common.log_level import LogLevel
from bear_dereth.logger.protocols.logger_type import TypeLogger
from bear_dereth.typing_tools import TypeHint

if TYPE_CHECKING:
    from rich.color import ColorSystem
    from rich.live import Live
    from rich.segment import Segment

HighlighterType = Callable[[str, Text], Text] | Text
JUPYTER_DEFAULT_COLUMNS = 115
JUPYTER_DEFAULT_LINES = 100
WINDOWS: bool = sys.platform == "win32"

_null_highlighter = NullHighlighter()

ColorSys = Literal["auto", "standard", "256", "truecolor", "windows"]


@dynamic_methods(methods=METHOD_NAMES, delegate_to="_log")
class LogConsole[T: TextIO | IO](Console, TypeHint(TypeLogger)):
    """A Console from Rich that has added methods named after the logger methods."""

    def __init__(
        self,
        *,
        color_system: ColorSys | None = "auto",
        force_terminal: bool | None = None,
        force_jupyter: bool | None = None,
        force_interactive: bool | None = None,
        soft_wrap: bool = False,
        theme: Theme | None = None,
        stderr: bool = False,
        file: T | None = None,
        quiet: bool = False,
        width: int | None = None,
        height: int | None = None,
        style: StyleType | None = None,
        no_color: bool | None = None,
        tab_size: int = 8,
        record: bool = False,
        markup: bool = True,
        emoji: bool = True,
        emoji_variant: EmojiVariant | None = None,
        highlight: bool = True,
        log_time: bool = True,
        log_path: bool = True,
        log_time_format: str | FormatTimeCallable = "[%X]",
        highlighter: HighlighterType | None = ReprHighlighter(),  # type: ignore[assignment] # noqa: B008
        legacy_windows: bool | None = None,
        safe_box: bool = True,
        get_datetime: Callable[[], datetime] | None = None,
        get_time: Callable[[], float] | None = None,
        _environ: Mapping[str, str] | None = None,
        level: str | int | LogLevel = LogLevel.DEBUG,
    ) -> None:
        """A Console from Rich that has added methods named after the logger methods."""
        if _environ is not None:  # Copy of os.environ allows us to replace it for testing
            self._environ = _environ

        self.is_jupyter: bool = _is_jupyter() if force_jupyter is None else force_jupyter
        if self.is_jupyter:
            if width is None:
                jupyter_columns: str | None = self._environ.get("JUPYTER_COLUMNS")
                if jupyter_columns is not None and jupyter_columns.isdigit():
                    width = int(jupyter_columns)
                else:
                    width = JUPYTER_DEFAULT_COLUMNS
            if height is None:
                jupyter_lines: str | None = self._environ.get("JUPYTER_LINES")
                if jupyter_lines is not None and jupyter_lines.isdigit():
                    height = int(jupyter_lines)
                else:
                    height = JUPYTER_DEFAULT_LINES

        self.tab_size: int = tab_size
        self.record: bool = record
        self._markup: bool = markup
        self._emoji: bool = emoji
        self._emoji_variant: EmojiVariant | None = emoji_variant
        self._highlight: bool = highlight
        self.legacy_windows: bool = (
            (detect_legacy_windows() and not self.is_jupyter) if legacy_windows is None else legacy_windows
        )

        if width is None:
            columns: str | None = self._environ.get("COLUMNS")
            if columns is not None and columns.isdigit():
                width = int(columns) - self.legacy_windows
        if height is None:
            lines: str | None = self._environ.get("LINES")
            if lines is not None and lines.isdigit():
                height = int(lines)

        self.soft_wrap: bool = soft_wrap
        self._width: int | None = width
        self._height: int | None = height

        self._color_system: ColorSystem | None

        self._force_terminal: bool | None = None
        if force_terminal is not None:
            self._force_terminal = force_terminal

        self._file: T | None = file
        self.quiet: bool = quiet
        self.stderr: bool = stderr

        if color_system is None:
            self._color_system = None
        elif color_system == "auto":
            self._color_system = self._detect_color_system()
        else:
            self._color_system = COLOR_SYSTEMS[color_system]

        self._lock = threading.RLock()
        self._log_render = LogRender(
            show_time=log_time,
            show_path=log_path,
            time_format=log_time_format,
        )
        self.highlighter: HighlighterType = highlighter or _null_highlighter  # type: ignore[assignment]
        self.safe_box: bool = safe_box
        self.get_datetime: Callable[[], datetime] | Callable[..., datetime] = get_datetime or datetime.now
        self.get_time: Callable[[], float] = get_time or monotonic
        self.style: str | Style | None = style
        self.no_color: bool = no_color if no_color is not None else self._environ.get("NO_COLOR", "") != ""
        self.is_interactive: bool = (
            (self.is_terminal and not self.is_dumb_terminal) if force_interactive is None else force_interactive
        )
        self._record_buffer_lock = threading.RLock()
        self._thread_locals = ConsoleThreadLocals(theme_stack=ThemeStack(DEFAULT if theme is None else theme))
        self._record_buffer: list[Segment] = []
        self._render_hooks: list[RenderHook] = []
        self._live: Live | None = None
        self._is_alt_screen = False
        self.level: LogLevel = LogLevel.get(level, default=LogLevel.DEBUG)

    @property
    def file(self) -> T:
        """Get the file object to write to."""
        file = self._file or (sys.stderr if self.stderr else sys.stdout)
        file = getattr(file, "rich_proxied_file", file)
        if file is None:
            file = NULL_FILE
        return cast("T", file)

    @file.setter
    def file(self, new_file: T) -> None:
        """Set a new file object."""
        self._file = new_file

    def _log(self, level: LogLevel, msg: object, *args, **kwargs) -> None:
        """Log a message at the specified level.

        Args:
            level (LogLevel): The log level for the message. We aren't using this parameter in the current implementation,
            msg (object): The message to log.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        if level.value >= self.level.value:
            with self._lock:
                if not self.quiet:
                    # For exception logs, print the exception details with local variables for better debugging.
                    if level == LogLevel.EXCEPTION:
                        self.print_exception(show_locals=True)
                    self.log(msg, *args, **kwargs)


if __name__ == "__main__":
    from io import StringIO

    console: LogConsole[StringIO] = LogConsole(file=StringIO())
    console.info("This is an info message")
    value = console.file
    print(value.getvalue())  # Print the captured log messages from StringIO
    console.debug("This is a debug message")
    console.info("This is an info message")
