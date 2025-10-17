"""This module implements the BearBase database class."""

from collections.abc import Callable, Iterator
from typing import Any, Self

from bear_dereth.data_structs.lru_cache import LRUCache
from bear_dereth.datastore.columns import Columns
from bear_dereth.datastore.record import Record, Records
from bear_dereth.datastore.storage import (
    JSONLStorage,
    JsonStorage,
    Storage,
    StorageChoices,
    TomlStorage,
    XMLStorage,
    YamlStorage,
    get_storage,
)
from bear_dereth.datastore.tables.data import TableData
from bear_dereth.datastore.tables.handler import TableHandler
from bear_dereth.datastore.tables.table import Table
from bear_dereth.datastore.unified_data import UnifiedDataFormat
from bear_dereth.query import QueryProtocol


class BearBase[T: Storage]:
    """The main database class for Bear's datastore system."""

    ##########################################################################
    # Configuration defaults - override in subclasses or instances as needed #
    ##########################################################################
    table_class = Table
    default_table_name: str = "default"
    default_choice: StorageChoices = "jsonl"
    record_class = Record
    query_cache = LRUCache
    cache_capacity = 10
    ##########################################################################

    def __init__(self, *args, **kwargs) -> None:
        """Create a new BearBase instance.

        Special handling:
            - If first positional arg is ":memory:", automatically uses memory storage
        """
        if args and args[0] == ":memory:":
            kwargs["storage"] = "memory"
            args = args[1:]

        choice: StorageChoices = kwargs.pop("storage", self.default_choice)
        storage_type: type[T] = get_storage(choice)  # type: ignore[arg-type]
        self._current_table: str | None = kwargs.pop("current_table", None)
        self._storage: T = storage_type(*args, **kwargs)
        self._data: UnifiedDataFormat | None = self.storage.read()
        self.handler: TableHandler[T] = TableHandler(storage=self._storage, data=self.data).load()
        self._query_cache: LRUCache = self.query_cache[QueryProtocol, list[Record]](capacity=self.cache_capacity)

    @property
    def data(self) -> UnifiedDataFormat:
        """Get the current unified data format, loading from storage if necessary."""
        if self._data is None:
            self._data = UnifiedDataFormat()
            self.storage.write(self._data)
        return self._data

    @property
    def storage(self) -> T:
        """Get the storage instance used for this BearBase instance."""
        return self._storage

    @property
    def opened(self) -> bool:
        """Check if the storage is open."""
        return not self.storage.closed

    @property
    def current_table(self) -> str:
        """Get the current table name, defaulting to default_table_name if not set."""
        return self._current_table or self.default_table_name

    def set_table(self, name: str) -> None:
        """Set the current table for operations.

        Args:
            name: The name of the table to set as current.
        """
        if name not in self.tables():
            raise KeyError(f"Table '{name}' does not exist.")
        self._current_table = name

    def create_table(self, name: str, columns: list[Columns]) -> Table:
        """Create a new table with explicit schema.

        Args:
            name: Name of the table
            columns: List of Columns defining the schema

        Returns:
            The created Table instance
        """
        table_data: TableData = self.data.new_table(name, columns=columns)
        table: Table = self.table(name, table_data=table_data)
        self.set_table(name)
        return table

    def table(self, name: str, table_data: TableData | None = None) -> Table:
        """Get a table by name.

        Args:
            name: The name of the table to get.
            table_data: Optional TableData if creating a new table

        Returns:
            The table instance.

        Raises:
            KeyError: If table doesn't exist and no table_data provided
        """
        if self.handler.has(name):
            return self.handler.get(name)

        if table_data is None:
            raise ValueError(f"Table '{name}' does not exist. Use create_table() to create it first.")

        return self.handler.new(name, table_data=table_data)

    def tables(self) -> set[str]:
        """Get a set of all table names in the database.

        Returns:
            A set of table names.
        """
        if self.data.empty:
            return set()
        return set(self.data.keys())

    def drop_tables(self) -> None:
        """Drop all tables from the database. **CANNOT BE REVERSED!**"""
        self.storage.clear()
        self.handler.clear()
        self.handler.write()

    def drop_table(self, name: str) -> None:
        """Drop a specific table from the database. **CANNOT BE REVERSED!**

        Args:
            name: The name of the table to drop.
        """
        if name not in self.data.tables:
            raise KeyError(f"Table '{name}' does not exist.")
        self.data.delete_table(name)
        del self.handler[name]
        self.storage.write(self.data)

    def insert(self, record: Any | None = None, **kwargs) -> None:
        """Insert a record into a specified or default table.

        Args:
            record: The record to insert
            **kwargs: Record fields as keyword arguments
        """
        if record is None and not kwargs:
            return
        if record is not None and not isinstance(record, dict):
            raise TypeError("Record must be a dictionary.")
        if record is None:
            record = kwargs
        self.table(self.current_table).insert(Record(**record))
        self.handler.write()

    def insert_multiple(self, records: list[Any]) -> None:
        """Insert multiple records into the default table.

        Args:
            records: A list of records to insert.
        """
        for record in records:
            if not isinstance(record, dict):
                raise TypeError("Each record must be a dictionary.")
            self.table(self.current_table).insert(Record(**record))

    def all(self) -> list[Record]:
        """Get all records from the default table.

        Returns:
            A list of all records in the default table.
        """
        return self.table(self.current_table).all()

    def search(self, query: QueryProtocol) -> Records:
        """Search for records in the default table matching a query.

        Args:
            query: The query to search for.

        Returns:
            A list of records matching the query.
        """
        cached_results: list[Record] | None = self._query_cache.get(query)
        if cached_results is not None:
            return cached_results
        return self.table(self.current_table).search(query)

    def get(self, cond: QueryProtocol | None = None, default: Record | None = None, **pk_kwargs) -> Records:
        """Get a single record from the default table matching a condition.

        Args:
            cond: The condition to match.
            default: The default value to return if no record is found.
            **pk_kwargs: Primary key fields as keyword arguments

        Returns:
            The matching record or the default value.
        """
        return self.table(self.current_table).get(cond, default, **pk_kwargs)

    def contains(self, query: QueryProtocol) -> bool:
        """Check if any record in the default table matches a query.

        Args:
            query: The query to check.

        Returns:
            True if any record matches the query, False otherwise.
        """
        return self.table(self.current_table).contains(query)

    def update(
        self, fields: dict | Callable[[Record], None] | None = None, cond: QueryProtocol | None = None, **kwargs
    ) -> int:
        """Update records in the default table matching a condition.

        Args:
            fields: Dictionary of fields to update OR callable that modifies record in-place
            cond: The condition to match for records to update
            **kwargs: Field updates as keyword arguments

        Returns:
            Number of records updated
        """
        updated: int = self.table(self.current_table).update(fields=fields, cond=cond, **kwargs)
        if updated > 0:
            self.handler.write()
        return updated

    def upsert(
        self,
        record: dict | Record | None = None,
        cond: QueryProtocol | None = None,
        **kwargs,
    ) -> None:
        """Update existing record or insert new one in the default table.

        Args:
            record: Record data to upsert
            cond: Query condition to find existing record
            **kwargs: Field values as keyword arguments
        """
        if record is None and not kwargs:
            return
        if record is not None and not isinstance(record, (dict | Record)):
            raise TypeError("Record must be a dictionary or Record instance.")
        self.table(self.current_table).upsert(record=record, cond=cond, **kwargs)
        self.handler.write()

    def close(self) -> None:
        """Close the storage instance."""
        self.storage.close()

    def save(self) -> None:
        """Save any changes to the storage."""
        self.handler.write()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args) -> None:
        """Close the storage instance when leaving a context."""
        if self.opened:
            self.close()

    def __getattr__(self, name: str) -> Any:
        """Forward all unknown attribute calls to the default table instance."""
        return getattr(self.table(self.current_table), name)

    def __len__(self) -> int:
        """Return the number of documents in the default table."""
        return len(self.table(self.current_table))

    def __iter__(self) -> Iterator[Record]:
        """Return an iterator for the default table's documents."""
        return iter(self.table(self.current_table))

    def __repr__(self) -> str:
        cls_name: str = self.__class__.__name__
        srg_name: str = self.storage.__class__.__name__
        tables: list[str] = list(self.tables())
        return f"<{cls_name} using {srg_name} with tables: {tables}, current_table='{self.current_table}'>"


class JSONLBase(BearBase[JSONLStorage]):
    """A BearBase subclass using JSONL storage by default."""

    default_storage: StorageChoices = "jsonl"


class JsonBase(BearBase[JsonStorage]):
    """A BearBase subclass using JSON storage by default."""

    default_storage: StorageChoices = "json"


class TomlBase(BearBase[TomlStorage]):
    """A BearBase subclass using TOML storage by default."""

    default_storage: StorageChoices = "toml"


class XMLBase(BearBase[XMLStorage]):
    """A BearBase subclass using XML storage by default."""

    default_storage: StorageChoices = "xml"


class YamlBase(BearBase[YamlStorage]):
    """A BearBase subclass using YAML storage by default."""

    default_storage: StorageChoices = "yaml"


__all__ = [
    "BearBase",
    "JSONLBase",
    "JsonBase",
    "TomlBase",
    "XMLBase",
    "YamlBase",
]
