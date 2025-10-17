"""This module implements tables, the central place for accessing and manipulating documents."""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Any, Self

from bear_dereth.data_structs.lru_cache import LRUCache
from bear_dereth.datastore.record import NullRecords, Record, Records
from bear_dereth.datastore.tables.protocol import TableProtocol
from bear_dereth.query import QueryProtocol

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from bear_dereth.datastore.columns import Columns
    from bear_dereth.datastore.tables.data import TableData


class Table(TableProtocol[Record]):
    """A table in the datastore, managing records and providing query capabilities."""

    default_query_cache_capacity = 10

    def __init__(
        self,
        name: str,
        table_data: TableData,
        save_callback: Callable[[], None],
        cache_size: int = default_query_cache_capacity,
    ) -> None:
        """Create a table instance."""
        self._name: str = name
        self._query_cache: LRUCache = LRUCache[QueryProtocol, Records](capacity=cache_size)
        self._table_data: TableData = table_data
        self._save_callback: Callable[[], None] = save_callback

    @property
    def name(self) -> str:
        """Get the table name."""
        return self._name

    @property
    def table_data(self) -> TableData:
        """Get the current table data, loading from storage if necessary."""
        return self._table_data

    @property
    def cache(self) -> LRUCache[QueryProtocol, Records]:
        """Get the query cache."""
        return self._query_cache

    def save(self) -> None:
        """Save the current state of the table to storage."""
        self._save_callback()
        self.cache.clear()

    def insert(self, record: dict | Record | None = None, **kwargs) -> None:
        """Insert a new record into the table.

        Args:
            record: Dictionary or Record instance to insert
            **kwargs: Field values as keyword arguments
        """
        if record is None:
            record = Record(**kwargs)
        elif isinstance(record, dict):
            record = Record(**record)
        self.table_data.add_record(record)
        self.save()

    def get(
        self,
        cond: QueryProtocol | None = None,
        default: Any = NullRecords,
        **pk_kwargs,
    ) -> Records:
        """Get a single record by primary key or query.

        Args:
            cond: Query condition to match
            default: Value to return if no record is found
            **pk_kwargs: Primary key field values as keyword arguments
        """
        if pk_kwargs:
            for rec in self.table_data.records:
                if all(rec.get(k) == v for k, v in pk_kwargs.items()):
                    return Records(record=rec)
            return default
        if cond:
            return self.search(cond)

        raise ValueError("Must provide either primary key kwargs or query condition")

    def set(self, key: str, value: Any) -> None:
        """Set a key-value pair.

        Args:
            key: The key to set in the record.
            value: The value to set for the key.
        """
        records: Records = self.get(key=key)
        if records is not NullRecords and records.count > 0:
            record: Record = records.first()
            print(f"Updating existing record for key '{key}' with value '{value}'")
            record[key] = value
        self.save()

    def search(self, query: QueryProtocol) -> Records:
        """Search for records matching a query."""
        cached: Records | None = self.cache.get(query)
        if cached is not None:
            if cached is NullRecords:
                return NullRecords
            return cached
        results: Records = Records([rec for rec in self.table_data.records if query(rec)])

        if query.is_cacheable:
            self.cache[query] = results if results.count > 0 else NullRecords
        return results

    def all(self) -> list[Record]:
        """Get all records from the table.

        Returns:
            List of all records in the table
        """
        return self.table_data.records

    def update(
        self,
        fields: dict | Callable[[Record], None] | None = None,
        cond: QueryProtocol | None = None,
        **kwargs,
    ) -> int:
        """Update records matching a condition.

        Args:
            fields: Dictionary of field updates to apply OR a callable that modifies a record in-place
            cond: Query condition to match records for update
            **kwargs: Field updates as keyword arguments (only used if fields is dict or None)

        Returns:
            Number of records updated

        Examples:
            # Update with dict
            table.update({'status': 'active'}, cond=Q.id == 1)

            # Update with kwargs
            table.update(status='active', updated_at=datetime.now())

            # Update with callable
            def increment_count(rec):
                rec['count'] = rec.get('count', 0) + 1
            table.update(increment_count, cond=Q.active == True)

        """
        if fields is None and kwargs:
            fields = kwargs
        elif fields is None and not kwargs:
            raise ValueError("Must provide fields to update either as dict, callable, or kwargs")

        def updater(record: Record) -> None:
            if callable(fields):
                fields(record)
            elif isinstance(fields, dict):
                for k, v in fields.items():
                    record[k] = v

        updated_count: int = 0
        for record in self.table_data.records:
            if cond is None or cond(record):
                try:
                    updater(record)
                    updated_count += 1
                except Exception:
                    with suppress(Exception):
                        continue

        if updated_count > 0:
            self.save()

        return updated_count

    def upsert(self, record: dict | Record | None = None, cond: QueryProtocol | None = None, **kwargs) -> None:
        """Update existing record or insert new one.

        Args:
            record: Record data to upsert
            cond: Query condition to find existing record
            **kwargs: Field values as keyword arguments
        """
        if record is None:
            record = Record(**kwargs)
        elif isinstance(record, dict):
            record = Record(**record)

        if cond is not None:
            updated: int = self.update(fields=dict(record), cond=cond)
            if updated > 0:
                return

        self.insert(record)

    def contains(self, query: QueryProtocol) -> bool:
        """Check if any record matches the query."""
        return any(query(rec) for rec in self.table_data.records)

    def delete(self, cond: QueryProtocol | None = None, **pk_kwargs) -> int:
        """Delete records matching a condition or primary key.

        Args:
            cond: Query condition to match records for deletion
            **pk_kwargs: Primary key field values as keyword arguments
        Returns:
            Number of records deleted
        """
        to_delete: list[Record] = []
        if pk_kwargs:
            for rec in self.table_data.records:
                if all(rec.get(k) == v for k, v in pk_kwargs.items()):
                    to_delete.append(rec)
        elif cond:
            to_delete = [rec for rec in self.table_data.records if cond(rec)]
        else:
            raise ValueError("Must provide either primary key kwargs or query condition")

        for rec in to_delete:
            self.table_data.delete(rec)

        deleted_count: int = len(to_delete)
        if deleted_count > 0:
            self.save()

        return deleted_count

    def columns(self) -> list[str]:
        """Get a list of all column names in the table."""
        columns: list[Columns] = self.table_data.columns
        return [col.name for col in columns]

    def records(self) -> Records:
        """Get all records in the table as a Records instance."""
        return Records(self.table_data.records)

    def clear(self) -> None:
        """Clear all records in the table."""
        self.table_data.clear()
        self.cache.clear()

    def close(self) -> None:
        """Close the table, releasing any resources."""
        self.cache.clear()

    def __call__(self) -> Self:
        """Reload the table data from storage."""
        return self

    def __len__(self) -> int:
        """Get the number of records in the table."""
        return len(self.table_data)

    def __iter__(self) -> Iterator[Record]:
        """Iterate over the records in the table."""
        return self.table_data.iterate()
