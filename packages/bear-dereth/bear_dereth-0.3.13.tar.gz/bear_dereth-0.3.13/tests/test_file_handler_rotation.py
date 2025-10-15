from __future__ import annotations

from typing import TYPE_CHECKING

from bear_dereth.logger.common.log_level import LogLevel
from bear_dereth.logger.core.config import ConsoleOptions, FileConfig, LoggerConfig
from bear_dereth.logger.handlers.file_handler import FileHandler
from bear_dereth.models.type_fields import PathModel

if TYPE_CHECKING:
    from pathlib import Path


class DummyConsole:
    """Minimal console replacement that writes to the handler's file."""

    def __init__(self, file_handler: FileHandler) -> None:
        """Initialize the DummyConsole with the handler's file."""
        self.file = file_handler.file

    def log(self, message: object, **_: object) -> None:
        """Write a message to the file."""
        self.file.write(f"{message}\n")


def build_handler(tmp_path: Path, *, max_size: int, rotations: int) -> FileHandler:
    """Create a FileHandler instance configured for testing."""
    file_path: Path = tmp_path / "logs" / "app.log"
    file_config = FileConfig(
        disable=False,
        max_size=max_size,
        rotations=rotations,
        path=PathModel().set(file_path),
        mode="a",
        encoding="utf-8",
        overrides={},
        respect_handler_level=True,
    )
    config = LoggerConfig(file=file_config)

    def err(message: str, **kwargs) -> None:
        raise AssertionError(f"Unexpected error callback: {message}")

    handler = FileHandler(
        name="test-handler",
        config=config,
        console_options=ConsoleOptions(theme=None),
        error_callback=err,
        root_level=lambda: LogLevel.DEBUG,
        level=LogLevel.DEBUG,
    )
    handler.caller = DummyConsole(handler)
    return handler


def test_rotate_moves_current_file_and_resets_base(tmp_path: Path) -> None:
    handler: FileHandler = build_handler(tmp_path, max_size=32, rotations=2)

    try:
        handler.file.write("A" * 40)
        handler.file.flush()

        assert handler.above_max_size

        handler.emit("first-message", style="", level=LogLevel.INFO)

        rotated: Path = handler.file_path.with_suffix(f".0{handler.file_path.suffix}")
        assert rotated.exists()
        assert rotated.read_text() == "A" * 40

        assert handler.file_path.exists()
        current_text: str = handler.file_path.read_text()
        assert "first-message" in current_text
        assert handler.file_size <= handler.max_size
    finally:
        handler.close()


def test_rotate_shifts_files_and_discards_oldest(tmp_path: Path) -> None:
    handler: FileHandler = build_handler(tmp_path, max_size=32, rotations=2)

    def fill_with(content: str, label: str) -> None:
        handler.file.write(content)
        handler.file.flush()
        handler.emit(label, style="", level=LogLevel.INFO)

    rotated_zero: Path = handler.file_path.with_suffix(f".0{handler.file_path.suffix}")
    rotated_one: Path = handler.file_path.with_suffix(f".1{handler.file_path.suffix}")

    try:
        # First overflow: base file should rotate into app.log.0 and capture only the raw payload.
        fill_with("A" * 40, "first")
        assert rotated_zero.read_text() == "A" * 40
        assert not rotated_one.exists()
        assert handler.file_path.read_text() == "first\n"

        # Second overflow: existing app.log.0 shifts to .1 and the previous base contents move into app.log.0.
        fill_with("B" * 40, "second")
        assert rotated_zero.exists()
        assert rotated_one.exists()
        assert rotated_zero.read_text() == "first\n" + ("B" * 40)
        assert rotated_one.read_text() == "A" * 40
        assert handler.file_path.read_text() == "second\n"

        # Third overflow: .0 becomes .1, .1 is dropped, and the latest base contents become the new .0.
        fill_with("C" * 40, "third")
        assert rotated_zero.read_text() == "second\n" + ("C" * 40)
        assert rotated_one.read_text() == "first\n" + ("B" * 40)
        assert handler.file_path.read_text() == "third\n"
    finally:
        handler.close()
