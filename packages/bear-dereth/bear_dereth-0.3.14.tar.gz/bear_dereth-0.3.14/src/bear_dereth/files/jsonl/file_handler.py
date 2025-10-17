"""A module for handling JSON Lines (JSONL) files with caching and file locking."""

from __future__ import annotations

from collections.abc import Iterable
import json
from typing import IO, TYPE_CHECKING, Any

from bear_dereth.files.base_file_handler import BaseFileHandler
from bear_dereth.files.file_lock import FileLock
from bear_dereth.stringing import to_lines

if TYPE_CHECKING:
    from pathlib import Path


class JSONLFilehandler[File_T](BaseFileHandler[list[File_T]]):
    """A simple JSONL file handler for reading and writing JSON Lines files."""

    def __init__(self, file: str | Path, mode: str = "a+", encoding: str = "utf-8") -> None:
        """Initialize the handler with the path to the JSONL file."""
        super().__init__(file, mode=mode, encoding=encoding)

    @staticmethod
    def filter(data: list[Any]) -> list[dict | str]:
        """Filter out invalid entries from the data.

        Args:
            data: A list of dictionaries or strings to be filtered.

        Returns:
            A list of valid dictionaries or strings.
        """
        return [ln for ln in data if (isinstance(ln, str) and ln.strip()) or isinstance(ln, dict)]

    def prepare(self, data: list[dict | str] | Iterable) -> list[str]:
        """Prepare data for writing to the JSONL file.

        Args:
            data: A list of dictionaries or strings to be written to the file.

        Returns:
            A list of strings, each representing a line in the JSONL file.
        """
        if isinstance(data, Iterable) and not isinstance(data, list):
            data = list(data)
        return [ln if isinstance(ln, str) else json.dumps(ln, ensure_ascii=False) for ln in self.filter(data)]

    def splitlines(self) -> list[str]:
        """Return all lines in the file as strings."""
        lines: list[File_T] = self.readlines()
        if all(isinstance(ln, dict) for ln in lines):
            return [json.dumps(ln, ensure_ascii=False) for ln in lines]
        return [str(ln) for ln in lines]

    @staticmethod
    def _internal_read(handle: IO[Any], n: int = -1) -> list[File_T]:
        data: list[Any] = []
        with FileLock(handle):
            handle.seek(0)
            raw: str = handle.read(n)
            if not raw.strip():
                return data
            for index, line in enumerate(to_lines(raw)):
                try:
                    record: dict | Any = json.loads(line, strict=False)
                    if not isinstance(record, dict):
                        raise TypeError(f"Line {index + 1} is not a JSON object: {line}")
                    data.append(record)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Error decoding JSONL data on line {index + 1}: {e}") from e
            return data

    def read(self, **kwargs) -> list[File_T]:
        """Read data from the JSON file."""
        handle: IO | None = self.handle()
        if handle is None:
            return []
        return self._internal_read(handle, **kwargs)

    def readlines(self, start: int = 0, stop: int | None = None) -> list[File_T]:
        """Read all lines from the JSONL file.

        Args:
            start: The starting index of lines to read. Default is 0.
            stop: The ending index of lines to read. Default is -1 (read all).

        Returns:
            A list of dictionaries or strings read from the file.
        """
        handle: IO[Any] | None = self.handle()
        if handle is None:
            return []
        data: list[File_T] = self.read()
        return data[start:stop] if stop is not None else data[start:]

    def readline(self, size: int = -1) -> File_T | str:
        """Read a single line from the JSONL file.

        Args:
            size: The index of the line to read. Default is -1 (read the last line).

        Returns:
            A single dictionary or string read from the file, or an empty string if the file is empty.
        """
        lines = self.readlines()
        start: int = 0 if size >= 0 else max(0, len(lines) + size)
        stop: int | None = size + 1 if size >= 0 else None
        lines: list[File_T] = lines[start:stop] if stop is not None else lines[start:]
        return lines[0] if lines else ""

    def write(self, data: list[File_T], **_) -> None:
        """Write data to the JSON file, replacing existing content."""
        handle: IO[Any] | None = self.handle()
        if handle is None:
            raise ValueError("File handle is not available.")
        with FileLock(handle):
            handle.seek(0)
            handle.truncate(0)
            handle.flush()
            if isinstance(data, str):
                lines = to_lines(data)
            elif isinstance(data, dict):
                lines: list[str] = [json.dumps(record, ensure_ascii=False) for record in data.values()]
            elif isinstance(data, list):
                lines: list[str] = [json.dumps(record, ensure_ascii=False) for record in data]
            else:
                raise TypeError("Input to write() must be a str, dict, or list.")
            handle.writelines(f"{line}\n" for line in lines)
            handle.flush()

    def writelines(self, lines: Iterable, offset: int = 0, whence: int = 2) -> None:
        """Append multiple lines to the JSONL file.

        Args:
            lines: An iterable of dictionaries or strings to be written to the file.
            offset: The offset to seek to before writing. Default is 0.
            whence: The reference point for the offset. Default is 2 (end of file

        Raises:
            TypeError: If the row is not a string or dictionary.
        """
        handle: IO[Any] | None = self.handle()
        if handle is None:
            raise ValueError("File handle is not available.")
        with FileLock(handle):
            handle.seek(offset, whence)
            for ln in self.prepare(lines):
                handle.write(f"{ln}\n")
            handle.flush()  # Force write to disk
