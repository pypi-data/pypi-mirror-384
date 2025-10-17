"""TOML storage backend for the datastore.

Provides TOML file storage using the unified data format.
"""

from __future__ import annotations

import tomllib
from typing import TYPE_CHECKING, Any

import tomlkit
from tomlkit import TOMLDocument
from tomlkit.api import inline_table

from bear_dereth.datastore.unified_data import UnifiedDataFormat
from bear_dereth.files.helpers import touch
from bear_dereth.files.text.file_handler import TextFileHandler

from .base_storage import Storage

if TYPE_CHECKING:
    from pathlib import Path

    from tomlkit.items import Array, InlineTable, Table


def get_arr() -> Array:
    """Return a new multiline TOML array."""
    arr: Array = tomlkit.array()
    arr.multiline(multiline=True)
    return arr


class TomlStorage(Storage):
    """A TOML file storage backend using the unified data format."""

    def __init__(self, file: str | Path, file_mode: str = "r+", encoding: str = "utf-8") -> None:
        """Initialize TOML storage.

        Args:
            file: Path to the TOML file
            file_mode: File mode for opening (default: "r+" for read/write)
            encoding: Text encoding to use (default: "utf-8")
        """
        super().__init__()
        self.file: Path = touch(file, mkdir=True)
        self.handler = TextFileHandler(self.file, mode=file_mode, encoding=encoding)

    def read(self) -> UnifiedDataFormat | None:
        """Read data from TOML file.

        Returns:
            UnifiedDataFormat instance or None if empty.

        Note:
            Extra fields in records not matching the schema columns are filtered out.
        """
        try:
            text: str = self.handler.read()
            data: dict[str, Any] = tomllib.loads(text)
            unified: UnifiedDataFormat = UnifiedDataFormat.model_validate(data)

            for _, table_data in unified.tables.items():
                valid_columns: set[str] = {col.name for col in table_data.columns}
                filtered_records: list[Any] = []
                for record in table_data.records:
                    filtered_record: dict[str, Any] = {k: v for k, v in record.items() if k in valid_columns}
                    filtered_records.append(filtered_record)
                table_data.records = filtered_records
            return unified
        except Exception:
            return None

    def write(self, data: UnifiedDataFormat) -> None:
        """Write data to TOML file with pretty inline formatting.

        Args:
            data: UnifiedDataFormat instance to write.
        """
        doc: TOMLDocument = tomlkit.document()

        header: Table = tomlkit.table()
        for k, v in sorted(data.header.items(), reverse=True):
            header[k] = v
        doc.add("header", header)

        tables: Table = tomlkit.table()
        for table_name, table_data in data.tables.items():
            table: Table = tomlkit.table()
            columns_arr: Array = get_arr()
            for col in table_data.columns:
                col_table: InlineTable = inline_table()
                for k, v in col.items():
                    col_table[k] = v
                columns_arr.append(col_table)
            table.add("columns", columns_arr)
            table.add("count", table_data.count)
            valid_columns: set[str] = {col.name for col in table_data.columns}
            records_arr: Array = get_arr()
            for record in table_data.records:
                record_table: InlineTable = inline_table()
                for key, value in record.items():
                    if key in valid_columns:
                        record_table[key] = value
                records_arr.append(record_table)
            table.add("records", records_arr)
            tables.add(table_name, table)
        doc.add("tables", tables)
        self.handler.write(tomlkit.dumps(doc))

    def close(self) -> None:
        """Close the file handle."""
        if self.closed:
            return
        self.handler.close()

    @property
    def closed(self) -> bool:
        """Check if the storage is closed."""
        return self.handler.closed


__all__ = ["TomlStorage"]
