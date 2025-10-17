"""A core data model for the unified data format used by all storage backends."""

from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator

from bear_dereth.datastore.columns import Columns
from bear_dereth.datastore.header_data import HeaderData
from bear_dereth.datastore.record import Record
from bear_dereth.datastore.tables.data import TableData
from bear_dereth.datastore.tables.holder import TablesHolder
from bear_dereth.models.general import ExtraIgnoreModel


class UnifiedDataFormat(ExtraIgnoreModel):
    """The unified in-memory data structure for all storage backends.

    This structure is used internally by all storage backends (JSONL, JSON, TOML, XML).
    Each format handles serialization/deserialization to/from this structure.

    Example structure:
        {
            "header": {
                "tables": ["users", "posts"],
                "version": "0.1.0"
            },
            "tables": {
                "users": {
                    "columns": [{"name": "id", "type": "int", ...}],
                    "count": 2,
                    "records": [{"id": 1, "name": "Bear"}, ...]
                }
            }
        }
    """

    header: HeaderData = Field(default_factory=HeaderData)
    tables: TablesHolder = TablesHolder()

    def new_table(
        self,
        name: str,
        columns: list[Columns] | None = None,
        table_data: TableData | None = None,
    ) -> TableData:
        """Create a new empty table and add it to the unified data format.

        Args:
            name: Name of the new table.
            columns: Optional list of Columns instances.

        Returns:
            The newly created TableData instance.
        """
        if name in self.tables:
            raise ValueError(f"Table '{name}' already exists.")
        if table_data is None:
            if columns is None or not columns:
                raise ValueError("Columns must be provided if table_data is not.")
            table: TableData = TableData.new(name=name, columns=columns)
        else:
            table = table_data
            table.name = name
        self.tables.add(name, table)
        self.header.add(table.name)
        return table

    def table(self, name: str) -> TableData:
        """Get a table by name.

        Args:
            name: Name of the table to get.

        Returns:
            The TableData instance.

        Raises:
            KeyError: If the table does not exist.
        """
        if name not in self.tables:
            raise KeyError(f"Table '{name}' does not exist.")
        return self.tables[name]

    def keys(self) -> list[str]:
        """Get a list of table names in the unified data format."""
        return list(self.tables.keys())

    def has(self, name: str) -> bool:
        """Alias for __contains__ to check if a table exists."""
        return self.__contains__(name)

    def get_table(self, name: str) -> TableData | None:
        """Retrieve a table by name.

        Args:
            name: Name of the table to retrieve.

        Returns:
            TableData instance if found, else None.
        """
        return self.tables.get(name)

    def delete_table(self, name: str) -> None:
        """Delete a table by name.

        Args:
            name: Name of the table to delete.
        """
        self.tables.remove(name)
        self.header.remove(name)

    def clear(self) -> None:
        """Clear all tables and reset the header."""
        self.tables.clear()
        self.header.tables.clear()

    def render(self) -> dict[str, Any]:
        """Render the unified data format as a dictionary."""
        return self.model_dump(exclude_none=True)

    @property
    def empty(self) -> bool:
        """Check if the unified data format is empty (no tables)."""
        return self.tables.empty

    def __contains__(self, name: str) -> bool:
        """Check if a table exists in the unified data format.

        Args:
            name: Name of the table to check.

        Returns:
            True if the table exists, else False.
        """
        return name in self.tables

    @model_validator(mode="before")
    @classmethod
    def validate_tables(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Ensure tables is a TablesHolder instance and inject table names."""
        tables: dict = values.get("tables", {})
        if not isinstance(tables, TablesHolder):
            tables_with_names: dict[str, Any] = {}
            for table_name, table_data in tables.items():
                if isinstance(table_data, dict) and "name" not in table_data:
                    table_data["name"] = table_name
                tables_with_names[table_name] = table_data
            values["tables"] = TablesHolder(root=tables_with_names)
        return values


if __name__ == "__main__":
    data = UnifiedDataFormat()
    data.new_table(
        name="users",
        columns=[
            Columns(name="id", type="int", primary_key=True, auto_increment=True),
            Columns(name="name", type="str"),
        ],
    )

    record = Record(name="Bear")
    data.table("users").insert(record)
    record2 = Record(root={"name": "Dereth"})
    data.table("users").insert(record2)

    print(data.model_dump_json(indent=4))
