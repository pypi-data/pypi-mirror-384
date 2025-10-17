"""Tests for TOML storage output and input."""

from pathlib import Path
from typing import Any

import pytest

from bear_dereth.datastore.storage import StorageChoices
from bear_dereth.datastore.storage.base_storage import Storage
from bear_dereth.datastore.storage.json import JsonStorage
from bear_dereth.datastore.storage.jsonl import JSONLStorage
from bear_dereth.datastore.storage.toml import TomlStorage
from bear_dereth.datastore.storage.xml import XMLStorage
from bear_dereth.datastore.storage.yaml import YamlStorage
from bear_dereth.datastore.tables.holder import TablesHolder
from bear_dereth.datastore.unified_data import HeaderData, TableData, UnifiedDataFormat


@pytest.fixture
def raw_data() -> dict[str, dict[str, Any]]:
    return {
        "header": {"version": "0.1.0", "tables": ["categories", "posts"]},
        "tables": {
            "categories": {
                "columns": [
                    {"name": "id", "type": "int", "nullable": False, "primary_key": True},
                    {"name": "name", "type": "str", "nullable": False},
                    {"name": "description", "type": "str", "nullable": True},
                ],
                "count": 2,
                "records": [
                    {"id": 1, "name": "Technology", "description": "All things tech and programming"},
                    {"id": 2, "name": "Personal"},
                ],
            },
            "posts": {
                "columns": [
                    {"name": "id", "type": "int", "nullable": False, "primary_key": True},
                    {"name": "category_id", "type": "int", "nullable": False},
                    {"name": "title", "type": "str", "nullable": False},
                    {"name": "published_at", "type": "datetime", "nullable": True},
                ],
                "count": 3,
                "records": [
                    {"id": 1, "category_id": 1, "title": "Why types are spicy", "published_at": "2025-10-01T12:30:00Z"},
                    {"id": 2, "category_id": 1, "title": "Event loops & you"},
                    {
                        "id": 3,
                        "category_id": 2,
                        "title": "A softer keyboard layout",
                        "published_at": "2025-09-14T08:00:00Z",
                    },
                ],
            },
        },
    }


@pytest.fixture
def get_unified_data(raw_data: dict[str, dict[str, Any]]) -> UnifiedDataFormat:
    unified: UnifiedDataFormat = UnifiedDataFormat.model_validate(raw_data)
    return unified


@pytest.fixture
def get_json_lines() -> list[str]:
    return [
        '{"$type": "header", "data": {"tables": ["categories", "posts"], "version": "0.1.0"}}',
        '{"$type": "schema", "table": "categories", "columns": [{"name": "id", "type": "int", "nullable": false, "primary_key": true}, {"name": "name", "type": "str", "nullable": false}, {"name": "description", "type": "str", "nullable": true}], "count": 2}',
        '{"$type": "record", "table": "categories", "data": {"id": 1, "name": "Technology", "description": "All things tech and programming"}}',
        '{"$type": "record", "table": "categories", "data": {"id": 2, "name": "Personal"}}',
        '{"$type": "schema", "table": "posts", "columns": [{"name": "id", "type": "int", "nullable": false, "primary_key": true}, {"name": "category_id", "type": "int", "nullable": false}, {"name": "title", "type": "str", "nullable": false}, {"name": "published_at", "type": "datetime", "nullable": true}], "count": 3}',
        '{"$type": "record", "table": "posts", "data": {"id": 1, "category_id": 1, "title": "Why types are spicy", "published_at": "2025-10-01T12:30:00Z"}}',
        '{"$type": "record", "table": "posts", "data": {"id": 2, "category_id": 1, "title": "Event loops & you"}}',
        '{"$type": "record", "table": "posts", "data": {"id": 3, "category_id": 2, "title": "A softer keyboard layout", "published_at": "2025-09-14T08:00:00Z"}}',
    ]


def test_toml_storage(get_unified_data: UnifiedDataFormat, tmp_path: Path) -> None:
    toml_path: Path = tmp_path / "test.toml"
    storage = TomlStorage(toml_path, file_mode="w+", encoding="utf-8")
    storage.write(get_unified_data)
    loaded: UnifiedDataFormat | None = storage.read()
    storage.close()
    assert loaded is not None
    assert isinstance(loaded, UnifiedDataFormat)
    assert loaded.header == get_unified_data.header
    assert loaded.tables == get_unified_data.tables
    tables: TablesHolder = loaded.tables
    assert "categories" in tables
    assert "posts" in tables
    assert tables["categories"].count == 2
    assert tables["posts"].count == 3
    assert tables["categories"].columns == get_unified_data.tables["categories"].columns
    assert tables["posts"].columns == get_unified_data.tables["posts"].columns
    assert tables["categories"].records == get_unified_data.tables["categories"].records
    assert tables["posts"].records == get_unified_data.tables["posts"].records


class TestTomlStorage:
    def test_toml_storage_empty(self, tmp_path: Path) -> None:
        """Test reading from an empty TOML file."""
        toml_path: Path = tmp_path / "empty.toml"
        storage = TomlStorage(toml_path, file_mode="w+", encoding="utf-8")
        storage.write(UnifiedDataFormat())
        loaded: UnifiedDataFormat | None = storage.read()
        assert loaded is not None
        storage.close()
        assert loaded == UnifiedDataFormat()

    def test_toml_storage_malformed(self, tmp_path: Path) -> None:
        """Test reading from a malformed TOML file."""
        toml_path: Path = tmp_path / "malformed.toml"
        toml_path.write_text("This is not valid TOML content!", encoding="utf-8")
        storage = TomlStorage(toml_path, file_mode="r", encoding="utf-8")
        loaded: UnifiedDataFormat | None = storage.read()
        assert loaded is None
        storage.close()

    def test_toml_storage_partial_data(self, tmp_path: Path) -> None:
        """Test reading from a TOML file with partial data."""
        toml_path: Path = tmp_path / "partial.toml"
        partial_toml = """
        [header]
        version = "0.1.0"
        tables = ["users"]

        [tables.users]
        columns = [
            {name = "id", type = "int", nullable = false, primary_key = true},
            {name = "username", type = "str", nullable = false}
        ]
        count = 1
        records = [
            {id = 1, username = "alice"}
        ]
        """
        toml_path.write_text(partial_toml.strip(), encoding="utf-8")
        storage = TomlStorage(toml_path, file_mode="r", encoding="utf-8")
        loaded: UnifiedDataFormat | None = storage.read()
        storage.close()
        assert loaded is not None
        assert loaded.header.version == "0.1.0"
        assert "users" in loaded.header.tables
        assert "users" in loaded.tables
        users_table: TableData = loaded.tables["users"]
        assert users_table.count == 1
        assert len(users_table.columns) == 2
        assert users_table.records == [{"id": 1, "username": "alice"}]

    def test_toml_storage_no_tables(self, tmp_path: Path) -> None:
        """Test reading from a TOML file with no tables defined."""
        toml_path: Path = tmp_path / "no_tables.toml"
        no_tables_toml = """
        [header]
        version = "0.1.0"
        tables = []
        """
        toml_path.write_text(no_tables_toml.strip(), encoding="utf-8")
        storage = TomlStorage(toml_path, file_mode="r", encoding="utf-8")
        loaded: UnifiedDataFormat | None = storage.read()
        storage.close()
        assert loaded is not None
        assert loaded.header.version == "0.1.0"
        assert loaded.header.tables == []
        assert loaded.tables.model_dump(exclude_none=True) == {}

    def test_toml_storage_no_header(self, tmp_path: Path) -> None:
        """Test reading from a TOML file with no header section."""
        toml_path: Path = tmp_path / "no_header.toml"
        no_header_toml = """
        [tables.users]
        columns = [
            {name = "id", type = "int", nullable = false, primary_key = true},
            {name = "username", type = "str", nullable = false}
        ]
        count = 1
        records = [
            {id = 1, username = "alice"}
        ]
        """
        toml_path.write_text(no_header_toml.strip(), encoding="utf-8")
        storage = TomlStorage(toml_path, file_mode="r", encoding="utf-8")
        loaded: UnifiedDataFormat | None = storage.read()
        storage.close()
        assert loaded is not None
        assert loaded.header == HeaderData()
        assert "users" in loaded.tables
        users_table: TableData = loaded.tables["users"]
        assert users_table.count == 1
        assert len(users_table.columns) == 2
        assert users_table.records == [{"id": 1, "username": "alice"}]

    def test_toml_storage_extra_fields(self, tmp_path: Path) -> None:
        """Test reading from a TOML file with extra unexpected fields."""
        toml_path: Path = tmp_path / "extra_fields.toml"
        extra_fields_toml = """
        [header]
        version = "0.1.0"
        tables = ["users"]
        extra_header_field = "should be ignored"

        [tables.users]
        columns = [
            {name = "id", type = "int", nullable = false, primary_key = true, extra_column_field = "ignore me"},
            {name = "username", type = "str", nullable = false}
        ]
        count = 1
        records = [
            {id = 1, username = "alice", extra_record_field = "ignore me too"}
        ]
        """
        toml_path.write_text(extra_fields_toml.strip(), encoding="utf-8")
        storage = TomlStorage(toml_path, file_mode="r", encoding="utf-8")
        loaded: UnifiedDataFormat | None = storage.read()
        storage.close()
        assert loaded is not None
        assert loaded.header.version == "0.1.0"
        assert "users" in loaded.header.tables
        assert "users" in loaded.tables
        users_table: TableData = loaded.tables["users"]
        assert users_table.count == 1
        assert len(users_table.columns) == 2
        assert users_table.records == [{"id": 1, "username": "alice"}]


class TestJsonStorage:
    def test_json_storage(self, get_unified_data: UnifiedDataFormat, tmp_path: Path) -> None:
        """Test reading and writing a JSON file."""
        json_path: Path = tmp_path / "test.json"
        storage = JsonStorage(json_path, file_mode="w+", encoding="utf-8")
        storage.write(get_unified_data)
        loaded: UnifiedDataFormat | None = storage.read()
        storage.close()
        assert loaded is not None
        assert isinstance(loaded, UnifiedDataFormat)
        assert loaded.header == get_unified_data.header
        assert loaded.tables == get_unified_data.tables
        tables: TablesHolder = loaded.tables
        assert "categories" in tables
        assert "posts" in tables
        assert tables["categories"].count == 2
        assert tables["posts"].count == 3
        assert tables["categories"].columns == get_unified_data.tables["categories"].columns
        assert tables["posts"].columns == get_unified_data.tables["posts"].columns
        assert tables["categories"].records == get_unified_data.tables["categories"].records
        assert tables["posts"].records == get_unified_data.tables["posts"].records

    def test_json_storage_empty(self, tmp_path: Path) -> None:
        """Test reading from an empty JSON file."""
        json_path: Path = tmp_path / "empty.json"
        storage = JsonStorage(json_path, file_mode="w+", encoding="utf-8")
        storage.write(UnifiedDataFormat())
        loaded: UnifiedDataFormat | None = storage.read()
        storage.close()
        assert loaded is not None
        assert loaded == UnifiedDataFormat()

    def test_json_storage_partial_data(self, tmp_path: Path) -> None:
        """Test reading from a JSON file with partial data."""
        json_path: Path = tmp_path / "partial.json"
        partial_data = UnifiedDataFormat(
            header=HeaderData(version="0.1.0", tables=["users"]),
            tables={
                "users": TableData(
                    name="users",
                    columns=[
                        {"name": "id", "type": "int", "nullable": False, "primary_key": True},
                        {"name": "username", "type": "str", "nullable": False},
                    ],  # pyright: ignore[reportArgumentType]
                    records=[{"id": 1, "username": "alice"}],  # pyright: ignore[reportArgumentType]
                )
            },
        )
        storage = JsonStorage(json_path, file_mode="w+", encoding="utf-8")
        storage.write(partial_data)
        loaded: UnifiedDataFormat | None = storage.read()
        storage.close()
        assert loaded is not None
        assert loaded.header.version == "0.1.0"
        assert "users" in loaded.header.tables
        assert "users" in loaded.tables
        users_table: TableData = loaded.tables["users"]
        assert users_table.count == 1
        assert len(users_table.columns) == 2
        assert users_table.records == [{"id": 1, "username": "alice"}]

    def test_json_storage_round_trip_fidelity(self, get_unified_data: UnifiedDataFormat, tmp_path: Path) -> None:
        """Test that data survives multiple write-read cycles without corruption."""
        json_path: Path = tmp_path / "round_trip.json"
        storage = JsonStorage(json_path, file_mode="w+", encoding="utf-8")
        # First cycle
        storage.write(get_unified_data)
        first_load: UnifiedDataFormat | None = storage.read()
        # Second cycle - write what we just read
        assert first_load is not None
        storage.write(first_load)
        second_load: UnifiedDataFormat | None = storage.read()
        storage.close()
        # Both loads should be identical to original
        assert first_load == get_unified_data
        assert second_load == get_unified_data
        assert first_load == second_load


class TestJSONLStorage:
    def test_jsonl_storage(self, get_json_lines: list[str], tmp_path: Path) -> None:
        """Test reading and writing a JSONL file."""
        jsonl_path: Path = tmp_path / "test.jsonl"
        storage = JSONLStorage(jsonl_path)
        storage.write_from_strings(get_json_lines)
        loaded: UnifiedDataFormat | None = storage.read()
        storage.close()
        assert loaded is not None
        assert isinstance(loaded, UnifiedDataFormat)

    def test_jsonl_storage_empty(self, tmp_path: Path) -> None:
        """Test reading from an empty JSONL file."""
        jsonl_path: Path = tmp_path / "empty.jsonl"
        storage = JSONLStorage(jsonl_path, file_mode="w+", encoding="utf-8")
        storage.write(UnifiedDataFormat())
        loaded: UnifiedDataFormat | None = storage.read()
        storage.close()
        assert loaded is not None
        assert loaded == UnifiedDataFormat()

    def test_jsonl_storage_partial_data(self, tmp_path: Path) -> None:
        """Test reading from a JSONL file with partial data."""
        jsonl_path: Path = tmp_path / "partial.jsonl"
        partial_jsonl = """
        {"$type": "header", "data": {"version": "0.1.0", "tables": ["users"]}}
        {"$type": "schema", "table": "users", "columns": [{"name": "id", "type": "int", "nullable": false, "primary_key": true}, {"name": "username", "type": "str", "nullable": false}]}
        {"$type": "record", "table": "users", "data": {"id": 1, "username": "alice"}}
        """
        jsonl_path.write_text(partial_jsonl.strip(), encoding="utf-8")
        storage = JSONLStorage(jsonl_path, file_mode="r", encoding="utf-8")
        loaded: UnifiedDataFormat | None = storage.read()
        storage.close()
        assert loaded is not None
        assert loaded.header.version == "0.1.0"
        assert "users" in loaded.header.tables
        assert "users" in loaded.tables
        users_table: TableData = loaded.tables["users"]
        assert users_table.count == 1
        assert len(users_table.columns) == 2
        assert users_table.records == [{"id": 1, "username": "alice"}]


class TestXMLStorage:
    def test_xml_storage(self, get_unified_data: UnifiedDataFormat, tmp_path: Path) -> None:
        """Test reading and writing an XML file."""
        xml_path: Path = tmp_path / "test.xml"
        storage = XMLStorage(xml_path, file_mode="w+", encoding="utf-8")
        storage.write(get_unified_data)
        loaded: UnifiedDataFormat | None = storage.read()
        storage.close()
        assert loaded is not None
        assert isinstance(loaded, UnifiedDataFormat)
        assert loaded.header == get_unified_data.header
        assert loaded.tables == get_unified_data.tables
        tables: TablesHolder = loaded.tables
        assert "categories" in tables
        assert "posts" in tables
        assert tables["categories"].count == 2
        assert tables["posts"].count == 3
        assert tables["categories"].columns == get_unified_data.tables["categories"].columns
        assert tables["posts"].columns == get_unified_data.tables["posts"].columns
        assert tables["categories"].records == get_unified_data.tables["categories"].records
        assert tables["posts"].records == get_unified_data.tables["posts"].records

    def test_xml_storage_empty(self, tmp_path: Path) -> None:
        """Test reading from an empty XML file."""
        xml_path: Path = tmp_path / "empty.xml"
        storage = XMLStorage(xml_path, file_mode="w+", encoding="utf-8")
        storage.write(UnifiedDataFormat())
        loaded: UnifiedDataFormat | None = storage.read()
        storage.close()
        assert loaded is not None
        assert loaded == UnifiedDataFormat()

    def test_xml_storage_partial_data(self, tmp_path: Path) -> None:
        """Test reading from an XML file with partial data."""
        xml_path: Path = tmp_path / "partial.xml"
        partial_data = UnifiedDataFormat(
            header=HeaderData(version="0.1.0", tables=["users"]),
            tables={
                "users": TableData(
                    name="users",
                    columns=[
                        {"name": "id", "type": "int", "nullable": False, "primary_key": True},
                        {"name": "username", "type": "str", "nullable": False},
                    ],  # pyright: ignore[reportArgumentType]
                    records=[{"id": 1, "username": "alice"}],  # pyright: ignore[reportArgumentType]
                )
            },
        )
        storage = XMLStorage(xml_path, file_mode="w+", encoding="utf-8")
        storage.write(partial_data)
        loaded: UnifiedDataFormat | None = storage.read()
        storage.close()
        assert loaded is not None
        assert loaded.header.version == "0.1.0"
        assert "users" in loaded.header.tables
        assert "users" in loaded.tables
        users_table: TableData = loaded.tables["users"]
        assert users_table.count == 1
        assert len(users_table.columns) == 2
        assert users_table.records == [{"id": 1, "username": "alice"}]

    def test_xml_storage_no_tables(self, tmp_path: Path) -> None:
        """Test reading from an XML file with no tables defined."""
        xml_path: Path = tmp_path / "no_tables.xml"
        no_tables_data = UnifiedDataFormat(header=HeaderData(version="0.1.0"))
        storage = XMLStorage(xml_path, file_mode="w+", encoding="utf-8")
        storage.write(no_tables_data)
        loaded: UnifiedDataFormat | None = storage.read()
        assert loaded is not None
        storage.close()
        assert loaded is not None
        assert loaded.header.version == "0.1.0"
        assert loaded.header.tables == []
        assert loaded.tables.model_dump(exclude_none=True) == {}

    def test_xml_storage_no_header(self, tmp_path: Path) -> None:
        """Test reading from an XML file with minimal header."""
        xml_path: Path = tmp_path / "no_header.xml"
        minimal_data = UnifiedDataFormat(
            tables={
                "users": TableData(
                    name="users",
                    columns=[
                        {"name": "id", "type": "int", "nullable": False, "primary_key": True},
                        {"name": "username", "type": "str", "nullable": False},
                    ],  # pyright: ignore[reportArgumentType]
                    records=[{"id": 1, "username": "alice"}],  # pyright: ignore[reportArgumentType]
                )
            }
        )
        storage = XMLStorage(xml_path, file_mode="w+", encoding="utf-8")
        storage.write(minimal_data)
        loaded: UnifiedDataFormat | None = storage.read()
        storage.close()
        assert loaded is not None
        assert "users" in loaded.tables
        users_table: TableData = loaded.tables["users"]
        assert users_table.count == 1
        assert len(users_table.columns) == 2
        assert users_table.records == [{"id": 1, "username": "alice"}]

    def test_xml_storage_type_preservation(self, tmp_path: Path) -> None:
        """Test that XML storage preserves different data types correctly."""
        xml_path: Path = tmp_path / "types.xml"
        type_test_data = UnifiedDataFormat(
            header=HeaderData(version="1.2.3", tables=["types_test"]),
            tables={
                "types_test": TableData(
                    name="types_test",
                    columns=[
                        {"name": "id", "type": "int", "nullable": False, "primary_key": True},
                        {"name": "count", "type": "int", "nullable": False},
                        {"name": "price", "type": "float", "nullable": False},
                        {"name": "active", "type": "bool", "nullable": False},
                        {"name": "name", "type": "str", "nullable": False},
                    ],  # pyright: ignore[reportArgumentType]
                    records=[
                        {"id": 1, "count": 42, "price": 19.99, "active": True, "name": "Widget"},
                        {"id": 2, "count": 0, "price": 0.0, "active": False, "name": "Gadget"},
                    ],  # pyright: ignore[reportArgumentType]
                )
            },
        )
        storage = XMLStorage(xml_path, file_mode="w+", encoding="utf-8")
        storage.write(type_test_data)
        loaded: UnifiedDataFormat | None = storage.read()
        assert loaded is not None
        storage.close()
        assert loaded is not None
        records = loaded.tables["types_test"].records
        # Check first record types
        assert isinstance(records[0]["id"], int)
        assert isinstance(records[0]["count"], int)
        assert isinstance(records[0]["price"], float)
        assert isinstance(records[0]["active"], bool)
        assert isinstance(records[0]["name"], str)
        # Check values
        assert records[0]["id"] == 1
        assert records[0]["count"] == 42
        assert records[0]["price"] == 19.99
        assert records[0]["active"] is True
        assert records[0]["name"] == "Widget"
        # Check second record
        assert records[1]["active"] is False
        assert records[1]["count"] == 0

    def test_xml_storage_round_trip_fidelity(self, get_unified_data: UnifiedDataFormat, tmp_path: Path) -> None:
        """Test that data survives multiple write-read cycles without corruption."""
        xml_path: Path = tmp_path / "round_trip.xml"
        storage = XMLStorage(xml_path, file_mode="w+", encoding="utf-8")
        # First cycle
        storage.write(get_unified_data)
        first_load: UnifiedDataFormat | None = storage.read()
        # Second cycle - write what we just read
        assert first_load is not None
        storage.write(first_load)
        second_load: UnifiedDataFormat | None = storage.read()
        assert second_load is not None
        storage.close()
        # Both loads should be identical to original
        assert first_load == get_unified_data
        assert second_load == get_unified_data
        assert first_load == second_load

    def test_xml_storage_missing_optional_fields(self, tmp_path: Path) -> None:
        """Test handling records with missing optional fields."""
        xml_path: Path = tmp_path / "optional.xml"
        optional_data = UnifiedDataFormat(
            header=HeaderData(version="0.1.0", tables=["products"]),
            tables={
                "products": TableData(
                    name="products",
                    columns=[
                        {"name": "id", "type": "int", "nullable": False, "primary_key": True},
                        {"name": "name", "type": "str", "nullable": False},
                        {"name": "description", "type": "str", "nullable": True},
                    ],  # pyright: ignore[reportArgumentType]
                    records=[
                        {"id": 1, "name": "Product A", "description": "A great product"},
                        {"id": 2, "name": "Product B"},  # Missing description
                        {"id": 3, "name": "Product C", "description": "Another product"},
                    ],  # pyright: ignore[reportArgumentType]
                )
            },
        )
        storage = XMLStorage(xml_path, file_mode="w+", encoding="utf-8")
        storage.write(optional_data)
        loaded: UnifiedDataFormat | None = storage.read()
        storage.close()
        assert loaded is not None
        records = loaded.tables["products"].records
        assert len(records) == 3
        assert "description" in records[0]
        assert "description" not in records[1] or records[1].get("description") is None
        assert "description" in records[2]


class TestYamlStorage:
    def test_yaml_storage(self, get_unified_data: UnifiedDataFormat, tmp_path: Path) -> None:
        """Test reading and writing a YAML file."""
        yaml_path: Path = tmp_path / "test.yaml"
        storage = YamlStorage(yaml_path, file_mode="w+", encoding="utf-8")
        storage.write(get_unified_data)
        loaded: UnifiedDataFormat | None = storage.read()
        storage.close()
        assert loaded is not None
        assert isinstance(loaded, UnifiedDataFormat)
        assert loaded.header == get_unified_data.header
        assert loaded.tables == get_unified_data.tables
        tables: TablesHolder = loaded.tables
        assert "categories" in tables
        assert "posts" in tables
        assert tables["categories"].count == 2
        assert tables["posts"].count == 3
        assert tables["categories"].columns == get_unified_data.tables["categories"].columns
        assert tables["posts"].columns == get_unified_data.tables["posts"].columns
        assert tables["categories"].records == get_unified_data.tables["categories"].records
        assert tables["posts"].records == get_unified_data.tables["posts"].records

    def test_yaml_storage_empty(self, tmp_path: Path) -> None:
        """Test reading from an empty YAML file."""
        yaml_path: Path = tmp_path / "empty.yaml"
        storage = YamlStorage(yaml_path, file_mode="w+", encoding="utf-8")
        storage.write(UnifiedDataFormat())
        loaded: UnifiedDataFormat | None = storage.read()
        storage.close()
        assert loaded is not None
        assert loaded == UnifiedDataFormat()

    def test_yaml_storage_partial_data(self, tmp_path: Path) -> None:
        """Test reading from a YAML file with partial data."""
        yaml_path: Path = tmp_path / "partial.yaml"
        partial_data = UnifiedDataFormat(
            header=HeaderData(version="0.1.0", tables=["users"]),
            tables={
                "users": TableData(
                    name="users",
                    columns=[
                        {"name": "id", "type": "int", "nullable": False, "primary_key": True},
                        {"name": "username", "type": "str", "nullable": False},
                    ],  # pyright: ignore[reportArgumentType]
                    records=[{"id": 1, "username": "alice"}],  # pyright: ignore[reportArgumentType]
                )
            },
        )
        storage = YamlStorage(yaml_path, file_mode="w+", encoding="utf-8")
        storage.write(partial_data)
        loaded: UnifiedDataFormat | None = storage.read()
        storage.close()
        assert loaded is not None
        assert loaded.header.version == "0.1.0"
        assert "users" in loaded.header.tables
        assert "users" in loaded.tables
        users_table: TableData = loaded.tables["users"]
        assert users_table.count == 1
        assert len(users_table.columns) == 2
        assert users_table.records == [{"id": 1, "username": "alice"}]

    def test_yaml_storage_round_trip_fidelity(self, get_unified_data: UnifiedDataFormat, tmp_path: Path) -> None:
        """Test that data survives multiple write-read cycles without corruption."""
        yaml_path: Path = tmp_path / "round_trip.yaml"
        storage = YamlStorage(yaml_path, file_mode="w+", encoding="utf-8")
        # First cycle
        storage.write(get_unified_data)
        first_load: UnifiedDataFormat | None = storage.read()
        assert first_load is not None
        # Second cycle - write what we just read
        storage.write(first_load)
        second_load: UnifiedDataFormat | None = storage.read()
        storage.close()
        # Both loads should be identical to original
        assert first_load == get_unified_data
        assert second_load == get_unified_data
        assert first_load == second_load


@pytest.mark.parametrize(
    ("storage_class", "file_extension"),
    [
        (JsonStorage, "json"),
        (TomlStorage, "toml"),
        (JSONLStorage, "jsonl"),
        (XMLStorage, "xml"),
        (YamlStorage, "yaml"),
    ],
)
def test_generate_sample_output_files(
    get_unified_data: UnifiedDataFormat, storage_class: type[Storage], file_extension: StorageChoices
) -> None:
    """Generate sample output files for all storage formats.

    This test creates a tests/data/ directory with sample files showing
    what each storage format looks like. Useful for documentation and debugging.
    """
    # Create tests/data directory
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)

    # Generate JSON sample
    json_path = data_dir / "sample.json"
    json_storage = JsonStorage(json_path, file_mode="w+", encoding="utf-8")
    json_storage.write(get_unified_data)
    json_storage.close()

    # Generate TOML sample
    toml_path = data_dir / "sample.toml"
    toml_storage = TomlStorage(toml_path, file_mode="w+", encoding="utf-8")
    toml_storage.write(get_unified_data)
    toml_storage.close()

    # Generate JSONL sample
    jsonl_path = data_dir / "sample.jsonl"
    jsonl_storage = JSONLStorage(jsonl_path, file_mode="w+", encoding="utf-8")
    jsonl_storage.write(get_unified_data)
    jsonl_storage.close()

    # Generate XML sample
    xml_path = data_dir / "sample.xml"
    xml_storage = XMLStorage(xml_path, file_mode="w+", encoding="utf-8")
    xml_storage.write(get_unified_data)
    xml_storage.close()

    # Generate YAML sample
    yaml_path = data_dir / "sample.yaml"
    yaml_storage = YamlStorage(yaml_path, file_mode="w+", encoding="utf-8")
    yaml_storage.write(get_unified_data)
    yaml_storage.close()

    # Verify all files were created
    assert json_path.exists()
    assert toml_path.exists()
    assert jsonl_path.exists()
    assert xml_path.exists()
    assert yaml_path.exists()

    # Verify they're not empty
    assert json_path.stat().st_size > 0
    assert toml_path.stat().st_size > 0
    assert jsonl_path.stat().st_size > 0
    assert xml_path.stat().st_size > 0
    assert yaml_path.stat().st_size > 0
