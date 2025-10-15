"""Bear's datastore - A clean, simple, and powerful document storage system.

This module provides a lightweight alternative to traditional databases.
Supports multiple storage backends (JSON, JSONL, TOML, in-memory) and advanced querying.
"""

from .columns import Columns
from .common import ValueType
from .database import BearBase, JsonBase, JSONLBase, TomlBase, XMLBase, YamlBase
from .header_data import HeaderData
from .record import Record
from .storage import StorageChoices
from .tables.data import TableData
from .tables.handler import TableHandler
from .tables.table import Table
from .unified_data import UnifiedDataFormat

__all__ = [
    "BearBase",
    "Columns",
    "HeaderData",
    "JSONLBase",
    "JsonBase",
    "Record",
    "StorageChoices",
    "Table",
    "TableData",
    "TableHandler",
    "TomlBase",
    "UnifiedDataFormat",
    "ValueType",
    "XMLBase",
    "YamlBase",
]
