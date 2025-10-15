"""Protocol for table-like storage interfaces."""

from typing import Any, Protocol, Self, runtime_checkable

from bear_dereth.query import QueryProtocol


@runtime_checkable
class TableProtocol[DataType](Protocol):
    """Protocol for table-like storage interfaces.

    This defines the interface that storage backends should implement
    for Bear's datastore system.
    """

    def __call__(self, *args: Any, **kwargs: Any) -> Self:
        """Make the table callable."""
        raise NotImplementedError("To be overridden!")

    def get(self, cond: QueryProtocol | None = None, default: DataType | None = None, **pk_kwargs) -> Any:
        """Get a value by key."""
        raise NotImplementedError("To be overridden!")

    def set(self, key: str, value: Any) -> None:
        """Set a key-value pair."""
        raise NotImplementedError("To be overridden!")

    def search(self, query: QueryProtocol) -> Any:
        """Search for records matching a query."""
        raise NotImplementedError("To be overridden!")

    def all(self) -> list[DataType]:
        """Get all records."""
        raise NotImplementedError("To be overridden!")

    def upsert(self, record: DataType, cond: QueryProtocol, **kwargs) -> None:
        """Update existing record or insert new one."""
        raise NotImplementedError("To be overridden!")

    def contains(self, query: QueryProtocol) -> bool:
        """Check if any record matches the query."""
        raise NotImplementedError("To be overridden!")

    def clear(self) -> None:
        """Clear all records in the table."""
        raise NotImplementedError("To be overridden!")

    def close(self) -> None:
        """Close the table/storage."""
        raise NotImplementedError("To be overridden!")


__all__ = ["TableProtocol"]
