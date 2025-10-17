"""A handler for managing multiple tables in the database."""

from typing import Self

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from bear_dereth.datastore.storage import Storage
from bear_dereth.datastore.tables.table import Table
from bear_dereth.datastore.unified_data import TableData, UnifiedDataFormat


@dataclass(slots=True, config=ConfigDict(arbitrary_types_allowed=True))
class TableHandler[T: Storage]:
    """A handler for managing multiple tables in the database."""

    storage: T
    data: UnifiedDataFormat = Field(default=...)
    tables: dict[str, Table] = Field(default_factory=dict)

    def write(self) -> None:
        """Write the current state of all tables to storage."""
        self.storage.write(self.data)

    def update_data(self, data: UnifiedDataFormat) -> Self:
        """Update the internal data representation."""
        self.data = data
        return self

    def load(self) -> Self:
        """Load all tables from storage into the handler."""
        for name, table_data in self.data.tables.items():
            table: Table = self.make(name=name, table_data=table_data)
            self.tables[name] = table
        return self

    def new(self, name: str, table_data: TableData) -> Table:
        """Create a new empty table and add it to the handler.

        Args:
            name: Name of the new table.

        Returns:
            The newly created Table instance.

        Raises:
            ValueError: If a table with the same name already exists.
        """
        if name in self.tables:
            raise ValueError(f"Table '{name}' already exists.")
        table: Table = self.make(name=name, table_data=table_data)
        self.tables[name] = table
        self.write()
        return table

    def get(self, name: str) -> Table:
        """Get a table by name."""
        if name not in self.tables:
            raise KeyError(f"Table '{name}' does not exist.")
        return self.tables[name]

    def has(self, name: str) -> bool:
        """Check if a table exists."""
        return name in self.tables

    def clear(self) -> None:
        """Clear all tables from the handler."""
        self.data.clear()
        self.tables.clear()

    def make(self, name: str, table_data: TableData) -> Table:
        """Map a TableData instance to a Table instance."""
        return Table(name=name, table_data=table_data, save_callback=self.write)

    def __getattr__(self, name: str) -> Table:
        """Get a table by name."""
        return self.get(name)

    def __delitem__(self, name: str) -> None:
        """Delete a table by name."""
        if name not in self.tables:
            raise KeyError(f"Table '{name}' does not exist.")
        del self.tables[name]

    def __setitem__(self, name: str, table: Table) -> None:
        """Set a table by name."""
        if name in self.tables:
            raise ValueError(f"Table '{name}' already exists.")
        self.tables[name] = table

    def __contains__(self, name: str) -> bool:
        """Check if a table exists in the handler."""
        return self.has(name)
