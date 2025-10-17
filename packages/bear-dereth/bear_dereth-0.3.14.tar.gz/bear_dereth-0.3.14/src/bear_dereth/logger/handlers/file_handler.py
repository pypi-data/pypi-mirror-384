"""File handler implementation for BearLogger."""

from __future__ import annotations

from pathlib import Path
from typing import IO, TYPE_CHECKING, Any, ClassVar, TextIO

from rich.console import Console

from bear_dereth.di import Provide, inject
from bear_dereth.files import touch
from bear_dereth.files.textio_utility import NULL_FILE
from bear_dereth.logger.common.log_level import LogLevel
from bear_dereth.logger.core.config import ConsoleOptions, Container, LoggerConfig
from bear_dereth.logger.protocols.handler import Handler

if TYPE_CHECKING:
    from collections.abc import Callable


def all_file_names(file_path: Path, max_rotations: int) -> list[Path]:
    """Generate rotated log file names based on the base file path and number of rotations."""
    if max_rotations <= 0:
        return []
    return [file_path.with_suffix(f".{i}{file_path.suffix}") for i in range(max_rotations)]


class FileHandler(Handler):
    """A handler that outputs messages to a file using Rich Console."""

    default_mode_attr: ClassVar[str] = "log"
    alt_mode_attr: ClassVar[str] = "log"

    @inject
    def __init__(
        self,
        *,
        name: str | None = None,
        file_path: str | Path | None = None,
        file_mode: str | None = None,
        encoding: str | None = None,
        config: LoggerConfig = Provide[Container.config],
        level: LogLevel | str | int = LogLevel.DEBUG,
        console_options: ConsoleOptions = Provide[Container.console_options],
        error_callback: Callable[..., Any] = Provide[Container.error_callback],
        root_level: Callable[[], LogLevel] = Provide[Container.root_level],
    ) -> None:
        """Initialize the FileHandler.

        Args:
            name: Optional name for the handler
            file_path: Path to the log file (as string or Path). If None, uses config value.
            file_mode: File open mode ('a' for append, 'w' for write). If None, uses config value.
            encoding: File encoding. If None, uses config value.
            level: Minimum logging level for this handler. If None, uses root logger level.
        """
        super().__init__()
        self.name: str | None = name
        self.config: LoggerConfig = config
        self.error_callback: Callable[..., Any] = error_callback
        self.get_level: Callable[..., LogLevel] = root_level
        self.level: LogLevel = LogLevel.get(level, default=self.get_level())
        self.file_path: Path = Path(file_path) if file_path else config.file.path()
        self.file_mode: str = file_mode if file_mode else config.file.mode
        self.encoding: str = encoding if encoding else config.file.encoding
        self.console_options: ConsoleOptions = console_options.model_copy()
        self.max_size: int = config.file.max_size
        self.max_rotations: int = config.file.rotations
        self.file: TextIO | IO = NULL_FILE
        self._log_files: list[Path] = all_file_names(self.file_path, self.max_rotations)
        self._file_base: str = self.file_path.stem
        self._file_suffix: str = self.file_path.suffix
        self._dir: Path = self.file_path.parent
        self.on_init()

    def on_init(self) -> None:
        """Hook for additional initialization if needed."""
        config_copy: ConsoleOptions = self.console_options.model_copy(update=self.config.file.overrides)
        config_copy.theme = None
        config_copy.markup = False
        config_copy.highlight = False
        config_copy.force_terminal = False
        config_copy.width = None
        if self.file is NULL_FILE:
            self.file = self.open(set_caller=False)
        self.caller = Console(file=self.file, **config_copy.model_dump(exclude_none=True))

    def open(self, set_caller: bool = True) -> IO[Any]:
        """Open the file and ensure the directory exists."""
        touch(self.file_path, mkdir=True)
        file: IO[Any] = self.file_path.open(mode=self.file_mode, encoding=self.encoding)
        if set_caller and self.caller:
            self.caller.file = file
        return file

    def emit(self, msg: object, style: str, level: LogLevel, **kwargs) -> None:  # noqa: ARG002
        """Emit a message to the file with the given style.

        Args:
            msg: The message to emit
            style: Rich style name to apply (may be stripped for plain text)
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments for Rich formatting
        """
        if self.caller and self.should_emit(level):
            if self.above_max_size:
                self.rotate()
            try:
                self.output_func()(msg, _stack_offset=2, **kwargs)
                self.file.flush() if self.file and not self.file.closed else None
            except Exception as e:
                self.error_callback("Error during FileHandler emit", error=e, name=self.name or "file_handler")

    def do_rotate(self, src: Path, dst: Path | None = None) -> None:
        """Rotate the current log file to the specified destination.

        Args:
            src: The source log file path (current log file)
            dst: The destination log file path (rotated log file). If None, uses src with .0 suffix.
        """
        if dst is None:
            dst = src.with_suffix(f".0{src.suffix}")
        if dst.exists():
            dst.unlink()
        if src.exists():
            src.rename(dst)

    def rotate(self) -> None:
        """Rotate the log files if the current file exceeds max size or if forced."""
        if self.max_rotations <= 0:
            return
        if self.file and not self.file.closed:
            self.file.close()
        try:
            for index in range(self.max_rotations - 1, 0, -1):
                self.do_rotate(self._log_files[index - 1], self._log_files[index])
            self.do_rotate(self.file_path, self._log_files[0])
        except Exception as e:  # pragma: no cover - guard against filesystem errors
            self.error_callback("Error during log rotation", error=e, name=self.name or "file_handler")
        finally:
            self.file = self.open()

    def close(self) -> None:
        """Close the handler and the underlying file."""
        if self.file and not self.file.closed:
            self.file.close()
            self.file = NULL_FILE

    @property
    def files_glob(self) -> str:
        """Get the glob pattern for log files managed by this handler."""
        return f"{self._file_base}.*{self._file_suffix}"

    @property
    def existing_files(self) -> list[Path]:
        """Get the list of log files managed by this handler."""
        return sorted(self._dir.glob(self.files_glob), key=lambda p: p.name, reverse=True)

    @property
    def file_size(self) -> int:
        """Get the current size of the log file."""
        try:
            return self.file_path.stat().st_size
        except (FileNotFoundError, OSError):
            return 0

    @property
    def above_max_size(self) -> bool:
        """Check if the log file exceeds the maximum size."""
        return self.max_size > 0 and self.file_size > self.max_size

    def __repr__(self) -> str:
        """String representation of the handler."""
        return f"FileHandler(file_path='{self.file_path}', level={self.level})"
