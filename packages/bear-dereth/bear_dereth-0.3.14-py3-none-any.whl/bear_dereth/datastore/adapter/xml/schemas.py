"""Module defining XML schema elements for the database."""

from typing import ClassVar, Literal

from pydantic import ConfigDict, Field, computed_field

from bear_dereth.models.xml_base_element import AbstractElement, BaseElement

XmlTypes = Literal[
    "str",
    "int",
    "float",
    "bool",
    "list",
    "dict",
    "None",
    "Columns",
    "TableData",
    "HeaderData",
    "UnifiedDataFormat",
]


class HelperModel[T: AbstractElement](BaseElement[T]):
    """XML element representing a conversion model."""

    type: XmlTypes = "str"


class VersionElement(HelperModel):
    """XML element representing the version of the database."""

    tag = "version"
    type: XmlTypes = "str"

    version: str


class SimpleTableElement(HelperModel):
    """XML element representing a simple table entry in the header."""

    tag = "table"
    type: XmlTypes = "str"

    name: str


class HeaderTablesElement(HelperModel[SimpleTableElement]):
    """XML element representing the tables list in the header."""

    tag = "tables"
    type: XmlTypes = "list"
    sub_elements: list[SimpleTableElement] = Field(default_factory=list)

    @computed_field
    def count(self) -> int:
        """Get the count of tables in the header."""
        return len(self.sub_elements)


class HeaderElement(HelperModel[VersionElement | HeaderTablesElement]):
    """XML element representing the header section of the database."""

    tag = "header"
    type: XmlTypes = "HeaderData"
    sub_elements: list[VersionElement | HeaderTablesElement] = Field(default_factory=list)


class ColumnElement(BaseElement):
    """XML element representing a single column in a table."""

    tag = "column"
    name: str
    type: str
    nullable: bool = False
    primary_key: bool | None = None


class RecordElement(BaseElement):
    """XML element representing a single record/row in a table.

    Records do not use HelperModel because they contain dynamic fields
    based on the table schema, not a static type annotation.
    """

    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)

    tag: ClassVar[str] = "record"


class ColumnsElement(HelperModel[ColumnElement]):
    """XML element representing the columns section of a table."""

    tag = "columns"
    type: XmlTypes = "list"
    sub_elements: list[ColumnElement] = Field(default_factory=list)
    meta: str = "Columns"

    @computed_field
    def count(self) -> int:
        """Get the count of columns in the table."""
        return len(self.sub_elements)


class RecordsElement(HelperModel[RecordElement]):
    """XML element representing the records section of a table."""

    tag = "records"
    type: XmlTypes = "list"
    sub_elements: list[RecordElement] = Field(default_factory=list)
    meta: str = "Record"

    @computed_field
    def count(self) -> int:
        """Get the count of records in the table."""
        return len(self.sub_elements)


class TableElement(HelperModel[ColumnsElement | RecordsElement]):
    """XML element representing a single table in the database."""

    tag = "table"
    type: XmlTypes = "TableData"
    sub_elements: list[ColumnsElement | RecordsElement] = Field(default_factory=list)

    name: str
    count: int = 2  # Always 2: one for columns, one for records


class TablesElement(HelperModel[TableElement]):
    """XML element representing the tables section of the database."""

    tag = "tables"
    type: XmlTypes = "dict"
    sub_elements: list[TableElement] = Field(default_factory=list)
    meta: str = "TableData"

    @computed_field
    def count(self) -> int:
        """Get the count of tables in the database."""
        return len(self.sub_elements)


class DatabaseElement(BaseElement[HeaderElement | TablesElement]):
    """XML element representing the root database."""

    tag = "database"
    type: XmlTypes = "UnifiedDataFormat"
    sub_elements: list[HeaderElement | TablesElement] = Field(default_factory=list)
