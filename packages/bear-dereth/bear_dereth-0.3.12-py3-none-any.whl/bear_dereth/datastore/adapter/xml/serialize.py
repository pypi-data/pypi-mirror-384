"""A module to serialize from UnifiedDataFormat to XML."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self
from xml.etree.ElementTree import ElementTree

from bear_dereth.datastore.adapter.xml.schemas import (
    ColumnElement,
    ColumnsElement,
    DatabaseElement,
    HeaderElement,
    HeaderTablesElement,
    RecordElement,
    RecordsElement,
    SimpleTableElement,
    TableElement,
    TablesElement,
    VersionElement,
)

if TYPE_CHECKING:
    from bear_dereth.datastore.record import Record
    from bear_dereth.datastore.unified_data import Columns, HeaderData, TableData, UnifiedDataFormat
    from bear_dereth.files.xml import Tree


class XMLSeralizer:
    """Serialize UnifiedDataFormat to self-describing XML format."""

    def __init__(self, data: UnifiedDataFormat) -> None:
        """Initialize the XML serializer with the given data."""
        self.data: UnifiedDataFormat = data

    def get_root(self, data: UnifiedDataFormat) -> DatabaseElement:
        """Serialize UnifiedDataFormat to root database element.

        Args:
            data: UnifiedDataFormat instance to serialize
        Returns:
            Root XML Element representing the entire database
        """
        root = DatabaseElement()
        header: HeaderElement = self.get_header(self.data.header)
        root.add(header)
        tables_elem = TablesElement()
        for table_name, table_data in data.tables.items():
            table_elem: TableElement = self.get_table(table_name, table_data)
            tables_elem.add(table_elem)
        root.add(tables_elem)
        return root

    def get_header(self, data: HeaderData) -> HeaderElement:
        """Serialize HeaderData to header element."""
        head: HeaderElement = HeaderElement()
        head.add(VersionElement(version=data.version))
        tables_elem = HeaderTablesElement()
        for table_name in data.tables:
            tables_elem.add(SimpleTableElement(name=table_name))
        head.add(tables_elem)
        return head

    def get_table(self, name: str, table_data: TableData) -> TableElement:
        """Serialize TableData to table element."""
        table_elem: TableElement = TableElement(name=name)
        columns_elem: ColumnsElement = ColumnsElement()
        for column in table_data.columns:
            col_elem: ColumnElement = self.get_column(column)
            columns_elem.add(col_elem)
        table_elem.add(columns_elem)
        records_elem: RecordsElement = RecordsElement()
        for record in table_data.records:
            record_elem: RecordElement = self.get_record(record)
            records_elem.add(record_elem)
        table_elem.add(records_elem)
        return table_elem

    def get_column(self, column: Columns) -> ColumnElement:
        """Serialize Columns model to column element."""
        col: dict[str, Any] = column.model_dump(exclude_none=True)
        return ColumnElement(**col)

    def get_record(self, record: Record) -> RecordElement:
        """Serialize record dict to record element."""
        rec: dict[str, Any] = record.model_dump(exclude_none=True)
        return RecordElement(**rec)

    def serialize(self) -> DatabaseElement:
        """Serialize the entire UnifiedDataFormat to an XML Element."""
        return self.get_root(self.data)

    def to_tree(self) -> Tree:
        """Convert the serialized XML to an ElementTree."""
        root_elem: DatabaseElement = self.serialize()
        return ElementTree(root_elem.to_xml())

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        pass
