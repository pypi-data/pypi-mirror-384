"""A base class for handling a single dedicated setting in a context-aware manner."""

from __future__ import annotations

from pathlib import Path
import shutil
from typing import TYPE_CHECKING, Any

from bear_dereth.config.settings_db_cls import SettingsModel
from bear_dereth.config.settings_manager import BearSettings
from bear_dereth.data_structs.space import Names
from bear_dereth.datastore.record import NullRecord, Record
from bear_dereth.query.query_mapping import QueryMapping, where
from bear_dereth.sentinels import NO_DEFAULT as DEFAULT

if TYPE_CHECKING:
    from pathlib import Path

    from bear_dereth.datastore.storage import StorageChoices
    from bear_dereth.datastore.tables.table import Table


class BaseSettingHandler:
    """Base Class for handling a single setting with specific focus that will change based upon the context of the server."""

    def __init__(self, name: str, path: str | Path | None = None, storage: StorageChoices = "toml") -> None:
        """Initialize the BaseSettingHandler with a name and optional path."""
        self.settings: BearSettings = BearSettings(name=name, path=path, storage=storage)
        if self.settings.file_path.exists():
            backup_path: Path = self.settings.file_path.with_suffix(".backup")
            if not backup_path.exists():
                shutil.copy(self.settings.file_path, backup_path)
        self.bases: Names[TableWrapper] = Names()
        self.register_table("settings", SettingsModel)

    def register_table[ValueType](self, name: str, model_cls: type[SettingsModel] = SettingsModel) -> None:
        """Register a new setting with a default value.

        This method is used to register a new setting dynamically.
        """
        if not hasattr(self.bases, name):
            table: Table = self.settings.db.create_table(name, columns=model_cls.get_columns())
            self.bases.add(name, TableWrapper(name, table))

    def get_table(self, name: str) -> TableWrapper:
        """Get a specific table by name."""
        return self.bases.get(name, strict=True)

    def __getattr__(self, k: str) -> TableWrapper:
        """Get a specific table by name using attribute access."""
        if self.bases.has(k):
            return self.bases.get(k, strict=True)
        raise AttributeError(f"'BaseSettingHandler' object has no attribute '{k}'")


class TableWrapper:
    """A wrapper for a table."""

    def __init__(self, name: str, table: Table, default: Any = DEFAULT) -> None:
        """Initialize the TableWrapper with a name and default value."""
        self.name: str = name
        self.table: Table = table
        self.default: Any = default

    @property
    def keys(self) -> list[str]:
        """Get all keys in the table."""
        records: list[Record] = self.table.records().all()
        return [record.key for record in records if record != NullRecord]

    @property
    def values(self) -> list[Any]:
        """Get all values in the table."""
        records: list[Record] = self.table.records().all()
        return [record.value for record in records if record != NullRecord]

    @property
    def items(self) -> list[tuple[str, Any]]:
        """Get all key-value pairs in the table."""
        records: list[Record] = self.table.records().all()
        return [(record.key, record.value) for record in records if record != NullRecord]

    def get(self, key: str) -> Any:
        """Get a value of the key in the table, returning the default if not found."""
        query: QueryMapping = where(key=key)
        record: Record = self.table.get(query=query.value).first()
        return record.value if record != NullRecord else self.default

    def set(self, key: str, v: Any) -> None:
        """Set a value of the key in the table."""
        self.table.set(key=key, value=v)

    def delete(self, key: str) -> None:
        """Delete a key from the table."""
        self.table.delete(key=key)
