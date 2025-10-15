"""Test BearBase-backed settings manager."""

from pathlib import Path
from typing import Any

import pytest

from bear_dereth.config import BearSettings, StorageChoices


def test_basic_settings_operations(tmp_path: Path) -> None:
    """Test basic get/set operations."""
    settings_file: Path = tmp_path / "settings.json"
    settings: BearSettings = BearSettings("test", path=str(settings_file))

    settings.set("theme", value="dark")
    settings.set("font_size", value=14)
    settings.set("auto_save", value=True)

    assert settings.get("theme") == "dark"
    assert settings.get("font_size") == 14
    assert settings.get("auto_save") is True

    settings.close()


def test_settings_persistence(tmp_path: Path) -> None:
    """Test that settings persist across instances."""
    settings_file: Path = tmp_path / "persist.json"

    settings1: BearSettings = BearSettings("test", path=str(settings_file))
    settings1.set("user", "Bear")
    settings1.set("version", "1.0.0")
    settings1.close()

    settings2: BearSettings = BearSettings("test", path=str(settings_file))
    assert settings2.get("user") == "Bear"
    assert settings2.get("version") == "1.0.0"
    settings2.close()


def test_update_existing_setting(tmp_path: Path) -> None:
    """Test updating an existing setting."""
    settings_file: Path = tmp_path / "update.json"
    settings: BearSettings = BearSettings("test", path=str(settings_file))

    settings.set("counter", 1)
    assert settings.get("counter") == 1

    settings.set("counter", 2)
    assert settings.get("counter") == 2

    settings.set("counter", 3)
    assert settings.get("counter") == 3

    settings.close()


def test_has_contains(tmp_path: Path) -> None:
    """Test checking if settings exist."""
    settings: BearSettings = BearSettings("test", path=str(tmp_path / "test.json"))

    assert not settings.has("missing")
    assert "missing" not in settings

    settings.set("exists", "yes")

    assert settings.has("exists")
    assert "exists" in settings

    settings.close()


def test_get_all_keys_values_items(tmp_path: Path) -> None:
    """Test getting all settings in various forms."""
    settings: BearSettings = BearSettings("test", path=str(tmp_path / "test.json"))

    settings.set("a", 1)
    settings.set("b", 2)
    settings.set("c", 3)

    assert len(settings) == 3
    assert set(settings.keys()) == {"a", "b", "c"}
    assert set(settings.values()) == {1, 2, 3}
    assert set(settings.items()) == {("a", 1), ("b", 2), ("c", 3)}

    all_settings: dict[str, Any] = settings.get_all()
    assert all_settings == {"a": 1, "b": 2, "c": 3}

    settings.close()


def test_context_manager(tmp_path: Path) -> None:
    """Test using settings as context manager."""
    settings_file: Path = tmp_path / "context.json"

    with BearSettings("test", path=str(settings_file)) as settings:
        settings.set("managed", value=True)
        assert settings.get("managed") is True

    with BearSettings("test", path=str(settings_file)) as settings:
        assert settings.get("managed") is True


def test_default_values(tmp_path: Path) -> None:
    """Test default values for missing keys."""
    settings: BearSettings = BearSettings("test", path=str(tmp_path / "test.json"))

    assert settings.get("missing") is None
    assert settings.get("missing", "default") == "default"
    assert settings.get("missing", 42) == 42

    settings.close()


def test_multiple_storage_backends(tmp_path: Path) -> None:
    """Test that settings work with different storage backends."""
    for storage_type in ["json", "toml"]:
        settings_file: Path = tmp_path / f"test.{storage_type}"
        settings: BearSettings = BearSettings(
            "test",
            path=str(settings_file),
            storage=storage_type,  # type: ignore[arg-type]
        )

        settings.set("backend", storage_type)
        settings.set("works", value=True)

        assert settings.get("backend") == storage_type
        assert settings.get("works") is True

        settings.close()


def test_dot_notation(tmp_path: Path) -> None:
    """Test dot notation for getting and setting values."""
    settings: BearSettings = BearSettings("test", path=str(tmp_path / "dot.json"))

    settings.theme = "dark"
    settings.font_size = 14
    settings.auto_save = True

    assert settings.theme == "dark"
    assert settings.font_size == 14
    assert settings.auto_save is True

    settings.theme = "light"
    assert settings.theme == "light"

    settings.close()


@pytest.fixture
def data_directory() -> Path:
    """Fixture to provide the data directory path."""
    return Path(__file__).parent / "data"


@pytest.fixture
def sample_data() -> list[tuple[str, str | int | float | bool]]:
    """Fixture to provide sample key-value pairs."""
    return [
        ("app_name", "Bear Dereth"),
        ("version", "1.0.0"),
        ("debug_mode", True),
        ("max_connections", 100),
        ("timeout_seconds", 30.5),
        ("theme", "dark"),
        ("language", "en"),
        ("auto_save", True),
        ("cache_size_mb", 512),
        ("log_level", "INFO"),
    ]


def create_settings_manager(name: str, path: Path, storage: StorageChoices) -> BearSettings:
    """Helper to create a BearSettings instance."""
    return BearSettings(
        name=name,
        path=path,
        file_name=f"{name}_settings.{storage}",
        storage=storage,
    )


@pytest.mark.parametrize("storage_type", ["json", "toml", "jsonl", "xml", "yaml"])
def test_generate_sample_bearbase_settings_output(
    data_directory: Path,
    sample_data: list[tuple],
    storage_type: StorageChoices,
):
    """Generate sample output files showing BearSettings in different formats.

    This test creates sample files in tests/data/ directory showing what
    BearSettings looks like with realistic data in different storage backends.
    Useful for documentation, debugging, and understanding the output format.
    """
    file_name: str = f"sample_settings.{storage_type}"
    settings_file: Path = data_directory / file_name
    if settings_file.exists():
        settings_file.unlink()

    settings: BearSettings = BearSettings(
        name="sample_settings",
        path=data_directory,
        file_name=file_name,
        storage=storage_type,
    )
    for key, value in sample_data:
        settings.set(key, value)
    settings.close()

    assert settings_file.exists(), f"{storage_type} sample file was not created"
    assert settings_file.stat().st_size > 0, f"{storage_type} sample file is empty"
    del settings

    # Reopen and verify data persists
    settings_verify = BearSettings(
        name="sample_app",
        path=data_directory,
        file_name=file_name,
        storage=storage_type,
    )

    assert settings_verify.get("app_name") == "Bear Dereth"
    assert settings_verify.get("debug_mode") is True
    assert settings_verify.get("max_connections") == 100
    assert settings_verify.get("timeout_seconds") == 30.5
    assert len(settings_verify.keys()) == len(sample_data)

    settings_verify.close()
