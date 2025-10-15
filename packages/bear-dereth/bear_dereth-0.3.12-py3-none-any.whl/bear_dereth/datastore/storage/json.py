"""JSON storage backend for the datastore.

Provides JSON file storage using the unified data format.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from bear_dereth.datastore.unified_data import UnifiedDataFormat
from bear_dereth.files.helpers import touch
from bear_dereth.files.json.file_handler import JSONFileHandler

from .base_storage import Storage

if TYPE_CHECKING:
    from pathlib import Path

    from bear_dereth.typing_tools import JSONLike


class JsonStorage(Storage):
    """A JSON file storage backend using the unified data format."""

    def __init__(self, file: str | Path, file_mode: str = "r+", encoding: str = "utf-8") -> None:
        """Initialize the JSON storage.

        Args:
            file: Path to the JSON file
            file_mode: File mode for opening (default: "r+" for read/write)
            encoding: Text encoding to use (default: "utf-8")
        """
        super().__init__()
        self.file: Path = touch(file, mkdir=True)
        self.handler: JSONFileHandler = JSONFileHandler(file=self.file, mode=file_mode, encoding=encoding)

    def read(self) -> UnifiedDataFormat | None:
        """Read data from the JSON file.

        Returns:
            UnifiedDataFormat instance or None if empty.

        Note:
            Extra fields in records not matching the schema columns are filtered out.
        """
        try:
            data: JSONLike = self.handler.read()
            tables: dict[str, dict[str, Any]] = data.get("tables", {})
            for table_data in tables.values():
                columns: list[dict[str, Any]] = table_data.get("columns", [])
                valid_columns: set[str] = {col["name"] for col in columns}
                records: list[dict[str, Any]] = table_data.get("records", [])
                filtered_records: list[dict[str, Any]] = []
                for record in records:
                    filtered_record: dict[str, Any] = {k: v for k, v in record.items() if k in valid_columns}
                    filtered_records.append(filtered_record)
                table_data["records"] = filtered_records
            return UnifiedDataFormat.model_validate(data)
        except Exception:
            return None

    def write(self, data: UnifiedDataFormat) -> None:
        """Write data to the JSON file, replacing existing content.

        Args:
            data: UnifiedDataFormat instance to write.

        Note:
            Records are filtered to only include fields matching the schema columns.
        """
        data_dict: dict[str, Any] = data.model_dump(exclude_none=True)
        tables: dict[str, dict[str, Any]] = data_dict.get("tables", {})
        for table_data in tables.values():
            columns: list[dict[str, Any]] = table_data.get("columns", [])
            valid_columns: set[str] = {col["name"] for col in columns}
            records: list[dict[str, Any]] = table_data.get("records", [])
            filtered_records: list[dict[str, Any]] = []
            for record in records:
                filtered_record: dict[str, Any] = {k: v for k, v in record.items() if k in valid_columns}
                filtered_records.append(filtered_record)
            table_data["records"] = filtered_records
        json_str: str = json.dumps(data_dict, indent=2)
        self.handler.write(json_str)

    def close(self) -> None:
        """Close all file handles."""
        if self.closed:
            return
        self.handler.close()

    @property
    def closed(self) -> bool:
        """Check if all file handles are closed."""
        return self.handler.closed


__all__ = ["JsonStorage"]
