"""TOML file handler for Bear Dereth."""

from __future__ import annotations

import tomllib
from typing import IO, TYPE_CHECKING, Any, Self

import tomlkit

from bear_dereth.files.base_file_handler import BaseFileHandler
from bear_dereth.files.file_lock import FileLock
from bear_dereth.files.text.file_handler import TextFileHandler

if TYPE_CHECKING:
    from pathlib import Path

TomlData = dict[str, Any]


class TomlFileHandler(BaseFileHandler[TomlData]):
    """TOML file handler with caching and utilities."""

    def __init__(self, file: Path | str) -> None:
        """Initialize the handler with a file path.

        Args:
            path: Path to the TOML file
        """
        super().__init__(file, mode="rb")
        self.txt_handler = TextFileHandler(file, mode="r+", encoding="utf-8")

    def read(self, **_) -> dict[str, Any]:
        """Read and parse TOML file, caching the result.

        Returns:
            Parsed TOML data as dictionary

        Raises:
            tomllib.TOMLDecodeError: If file contains invalid TOML
            ValueError: If file cannot be read
        """
        handle: IO[Any] | None = self.handle()
        if handle is None:
            raise ValueError("File handle is not available.")
        with FileLock(handle=handle, exclusive=False):
            try:
                return tomllib.load(handle)
            except tomllib.TOMLDecodeError as e:
                raise ValueError(f"Invalid TOML in {self.file}: {e}") from e
            except Exception as e:
                raise ValueError(f"Error reading TOML file {self.file}: {e}") from e

    def write(self, data: TomlData, **_) -> None:
        """Write data as TOML to file.

        Args:
            data: Data to serialize as TOML (must be dict-like)
            target_path: Path to write to (defaults to handler's path)

        Raises:
            TypeError: If data cannot be TOML serialized
            ValueError: If file cannot be written
        """
        handle: IO[Any] | None = self.handle()
        if handle is None:
            raise ValueError("File handle is not available.")
        try:
            self.txt_handler.write(self.to_string(data))
        except Exception as e:
            raise ValueError(f"Error writing TOML file {self.file}: {e}") from e

    def to_string(self, data: TomlData, sort_keys: bool = False) -> str:
        """Convert data to TOML string.

        Args:
            data: Data to serialize

        Returns:
            TOML formatted string

        Raises:
            ValueError: If data cannot be serialized
        """
        try:
            return tomlkit.dumps(data, sort_keys=sort_keys)
        except Exception as e:
            raise ValueError(f"Cannot serialize data to TOML: {e}") from e

    def get_section(
        self,
        data: TomlData | None,
        section: str,
        default: TomlData | None = None,
    ) -> dict[str, Any] | None:
        """Get a specific section from TOML data.

        Args:
            data: TOML data to search
            section: Section name (supports dot notation like 'tool.poetry')
            default: Default value if section not found

        Returns:
            Section data or default
        """
        current: TomlData = data or self.read()
        for key in section.split("."):
            if not isinstance(current, dict) or key not in current:
                return default
            current = current[key]
        return current if isinstance(current, dict) else default

    def update_section(self, section: str, data: TomlData) -> TomlData:
        """Update a specific section in TOML data.

        Args:
            section: Section path (supports dot notation like 'tool.poetry')
            data: Data to merge into section

        Returns:
            Modified TOML data
        """
        keys: list[str] = section.split(".")
        current: TomlData = self.read()

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            if not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]

        final_key: str = keys[-1]
        if final_key not in current or not isinstance(current[final_key], dict):
            current[final_key] = {}

        current[final_key].update(data)
        return current

    def __enter__(self) -> Self:
        """Enter context manager."""
        self.read()
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        """Exit context manager."""


__all__ = ["TomlData", "TomlFileHandler"]
