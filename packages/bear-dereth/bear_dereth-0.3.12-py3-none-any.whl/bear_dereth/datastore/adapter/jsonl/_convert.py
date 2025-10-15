"""Convert between JSONL lines and unified data format."""

import json
from typing import Any, TypedDict

from bear_dereth.data_structs.priority_queue import PriorityQueue
from bear_dereth.datastore.record import Record
from bear_dereth.datastore.unified_data import Columns, HeaderData, TableData, UnifiedDataFormat

from .line_types import HeaderLine, LinePrimitive, NullLine, OrderedLines, RecordLine, SchemaLine


def get_line_model(raw: dict[str, Any] | str) -> type[LinePrimitive]:
    """Get the appropriate line model based on the $type field."""
    try:
        line: dict[str, Any] = json.loads(raw) if isinstance(raw, str) else raw
        line_type: str | None = line.get("$type")
    except (json.JSONDecodeError, TypeError):
        return NullLine

    match line_type:
        case "header":
            return HeaderLine
        case "schema":
            return SchemaLine
        case "record":
            return RecordLine
    return NullLine


def get_schema_lines(lines: list[str]) -> list[SchemaLine]:
    """Extract schema lines from a list of JSONL strings."""
    schema_lines: list[SchemaLine] = []
    for line in lines:
        ln: type[LinePrimitive] = get_line_model(line)
        if isinstance(ln, type) and issubclass(ln, SchemaLine):
            schema_line: SchemaLine = SchemaLine.model_validate_json(line)
            schema_lines.append(schema_line)
    return schema_lines


def get_record_lines(lines: list[str]) -> list[RecordLine]:
    """Extract record lines from a list of JSONL strings."""
    record_lines: list[RecordLine] = []
    for line in lines:
        ln: type[LinePrimitive] = get_line_model(line)
        if isinstance(ln, type) and issubclass(ln, RecordLine):
            record_line: RecordLine = RecordLine.model_validate_json(line)
            record_lines.append(record_line)
    return record_lines


class Converter[T: UnifiedDataFormat]:
    def __init__(self, data: T | None = None, lines: list[Any] | None = None) -> None:
        self._output_data: T | None = data
        self._input_data: list[Any] = lines or []
        self.unified: UnifiedDataFormat = UnifiedDataFormat()
        self.queue: PriorityQueue[OrderedLines] = PriorityQueue[OrderedLines]()

    def to_json_lines(self, data: T | None = None) -> list[LinePrimitive]:
        """Convert to JSONL line format.

        Returns:
            List of line dictionaries with $type field for JSONL serialization.
        """
        if data is None:
            if self._output_data is None:
                return []
            data = self._output_data

        lines: list[LinePrimitive] = []
        lines.append(HeaderLine(data=data.header.model_dump()))
        for name, table_data in data.tables.items():
            schema = SchemaLine(
                table=name, columns=[col.render() for col in table_data.columns], count=len(table_data.records)
            )
            lines.append(schema)
            for record in table_data.records:
                lines.append(RecordLine(table=name, data=record.model_dump()))
        return lines

    @staticmethod
    def input_data_type(lines: list[Any]) -> type[LinePrimitive] | type[str] | type[OrderedLines]:
        if isinstance(lines, list) and lines:
            first: str | LinePrimitive | OrderedLines = lines[0]
            if isinstance(first, str):
                return str
            if isinstance(first, LinePrimitive):
                return LinePrimitive
            if isinstance(first, OrderedLines):
                return OrderedLines
            raise TypeError("Input data must be a list of strings or LinePrimitive instances.")
        raise ValueError("No lines to determine type.")

    def lines_handling(self, lines: list[Any]) -> None:
        line_type: type[LinePrimitive | str | OrderedLines] = self.input_data_type(lines)
        if line_type is str:
            for index, line in enumerate(lines):
                self.queue.put(OrderedLines(idx=index, line=line))
            return
        if line_type is OrderedLines:
            for line in lines:
                self.queue.put(line)
            return
        raise TypeError("Input data must be a list of strings or OrderedLines instances.")

    def from_jsonl_lines(self, lines: list[str] | list[OrderedLines] | None = None) -> UnifiedDataFormat:
        """Parse JSONL lines into unified format.

        Args:
            lines: List of parsed JSON objects from JSONL file.

        Returns:
            UnifiedDataFormat instance.
        """
        self.lines_handling(lines or self._input_data)
        self.queue.sort()
        if not self.queue:
            return UnifiedDataFormat()

        first: OrderedLines = self.queue.get()
        model_cls: type[LinePrimitive] = get_line_model(first.line)
        if not isinstance(model_cls, type) and issubclass(model_cls, HeaderLine):
            raise TypeError("The first line must be a header line.")
        header: HeaderLine = HeaderLine.model_validate_json(first.line)
        header_obj: HeaderData = HeaderData.model_validate(header.data)
        cls = UnifiedDataFormat(header=header_obj)
        tables: dict[str, TablesDict] = {}
        while self.queue:
            next_line: OrderedLines = self.queue.get()
            model_cls = get_line_model(next_line.line)
            if not isinstance(model_cls, type):
                continue
            created_line: LinePrimitive = model_cls.model_validate_json(next_line.line)
            table_name: str | None = created_line.table
            if table_name is None:
                continue
            if table_name not in tables:
                tables[table_name] = {
                    "name": table_name,
                    "columns": [],
                    "records": [],
                }
            if isinstance(created_line, SchemaLine):
                for col in created_line.columns or []:
                    tables[table_name]["columns"].append(Columns.model_validate(col))
            elif isinstance(created_line, RecordLine) and created_line.data is not None:
                tables[table_name]["records"].append(Record.model_validate(created_line.data))
        for table_data in tables.values():
            tbl = TableData(name=table_data["name"], columns=table_data["columns"], records=table_data["records"])
            cls.new_table(name=table_data["name"], table_data=tbl)
        return cls


class TablesDict(TypedDict):
    name: str
    columns: list[Columns]
    records: list[Record]


def to_jsonl_lines(data: UnifiedDataFormat) -> list[LinePrimitive]:
    converter: Converter[UnifiedDataFormat] = Converter(data=data)
    return converter.to_json_lines()


def from_jsonl_lines(lines: list[str] | list[OrderedLines]) -> UnifiedDataFormat:
    converter: Converter = Converter(lines=lines)
    return converter.from_jsonl_lines()
