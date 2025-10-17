"""JSONL storage backend for the datastore."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bear_dereth.datastore.adapter import LinePrimitive, OrderedLines
from bear_dereth.datastore.adapter.jsonl import from_jsonl_lines, to_jsonl_lines
from bear_dereth.files.helpers import touch
from bear_dereth.files.jsonl.file_handler import JSONLFilehandler

from .base_storage import Storage

if TYPE_CHECKING:
    from pathlib import Path

    from bear_dereth.datastore.unified_data import UnifiedDataFormat


class JSONLStorage(Storage):
    """A JSONL (JSON Lines) file storage backend.

    Each line in the file represents one JSON object/record.
    This format is append-friendly and easily parseable line-by-line.
    """

    def __init__(self, file: str | Path, file_mode: str = "a+", encoding: str = "utf-8") -> None:
        """Initialize JSONL storage.

        Args:
            file: Path to the JSONL file
            file_mode: File mode for opening (default: "a+" for read/append)
            encoding: Text encoding to use (default: "utf-8")
        """
        super().__init__()
        self.file: Path = touch(file, mkdir=True)
        self.file_mode: str = file_mode
        self.encoding: str = encoding
        self.handler: JSONLFilehandler = JSONLFilehandler(file=self.file, mode=file_mode, encoding=encoding)

    def read(self, **kwargs) -> UnifiedDataFormat | None:
        """Read data from JSONL file.

        Returns:
            UnifiedDataFormat instance or None if empty.

        Note:
            JSONL format stores structured lines with $type field.
            Lines are parsed into the unified format with header, schema, and records.
        """
        try:
            lines: list[str] = kwargs.pop("data", None) or self.readlines()
            if not lines:
                return None
            return from_jsonl_lines(lines)
        except Exception:
            return None

    def readlines(self) -> list[str]:
        """Read raw lines from the JSONL file."""
        return self.handler.splitlines()

    def ordered_lines(self, data: list[str] | None = None) -> list[OrderedLines]:
        """Read and parse lines into OrderedLines."""
        output_lines: list[OrderedLines] = []
        data = data or self.readlines()
        for index, line in enumerate(data):
            output_lines.append(OrderedLines(idx=index, line=line))
        return output_lines

    def write_from_strings(self, lines: list[str]) -> None:
        """Write raw JSONL lines to the file.

        Args:
            lines: List of JSON strings, each representing a line in JSONL format.
        """
        if not lines:
            return
        self.handler.clear()
        self.handler.writelines(lines)

    def write(self, data: UnifiedDataFormat) -> None:
        """Write data to JSONL file.

        Args:
            data: UnifiedDataFormat instance to write.
                  Converts to JSONL line format with header, schema, and record lines.
        """
        lines: list[LinePrimitive] = to_jsonl_lines(data)
        line_dicts: list[dict[str, Any]] = [line.render() for line in lines]
        self.handler.clear()
        if line_dicts:
            self.handler.writelines(line_dicts)

    def close(self) -> None:
        """Close the file handle."""
        if self.closed:
            return
        self.handler.close()

    @property
    def closed(self) -> bool:
        """Check if the storage is closed."""
        return self.handler.closed


__all__ = ["JSONLStorage"]
