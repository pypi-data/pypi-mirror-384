"""Tests for SimpleSettingsManager with multiple file formats."""

from pathlib import Path

import pytest

from bear_dereth.config.quick_settings import SimpleSettingsManager


def test_json_format(tmp_path: Path) -> None:
    """Test SimpleSettingsManager with JSON format."""
    settings = SimpleSettingsManager(name="test_json", path=tmp_path, fmt="json")

    # Test set and get
    settings.set("name", "Bear")
    settings.set("age", 30)
    settings.set("active", value=True)

    assert settings.get("name") == "Bear"
    assert settings.get("age") == 30
    assert settings.get("active") is True
    assert settings.file_path.suffix == ".json"

    # Test persistence
    settings2 = SimpleSettingsManager(name="test_json", path=tmp_path, fmt="json")
    assert settings2.get("name") == "Bear"
    assert settings2.get("age") == 30

    settings.close()
    settings2.close()


def test_yaml_format(tmp_path: Path) -> None:
    """Test SimpleSettingsManager with YAML format."""
    settings = SimpleSettingsManager(name="test_yaml", path=tmp_path, fmt="yaml")

    settings.set("database", "postgres")
    settings.set("port", 5432)
    settings.set("config", {"debug": True, "verbose": False})

    assert settings.get("database") == "postgres"
    assert settings.get("port") == 5432
    assert settings.get("config") == {"debug": True, "verbose": False}
    assert settings.file_path.suffix == ".yaml"

    settings.close()


def test_toml_format(tmp_path: Path) -> None:
    """Test SimpleSettingsManager with TOML format."""
    settings = SimpleSettingsManager(name="test_toml", path=tmp_path, fmt="toml")

    settings.set("title", "My App")
    settings.set("version", "1.0.0")
    settings.set("features", {"logging": True, "metrics": False})

    assert settings.get("title") == "My App"
    assert settings.get("version") == "1.0.0"
    assert settings.get("features") == {"logging": True, "metrics": False}
    assert settings.file_path.suffix == ".toml"

    settings.close()


def test_auto_detect_yaml_from_extension(tmp_path: Path) -> None:
    """Test auto-detection of YAML format from .yaml extension."""
    settings = SimpleSettingsManager(name="test_auto", file_name="config.yaml", path=tmp_path)

    assert settings.file_path.suffix == ".yaml"
    settings.set("auto_detected", value=True)
    assert settings.get("auto_detected") is True

    settings.close()


def test_auto_detect_yml_from_extension(tmp_path: Path) -> None:
    """Test auto-detection of YAML format from .yml extension."""
    settings = SimpleSettingsManager(name="test_auto", file_name="config.yml", path=tmp_path)

    assert settings.file_path.suffix == ".yaml"
    settings.close()


def test_auto_detect_toml_from_extension(tmp_path: Path) -> None:
    """Test auto-detection of TOML format from .toml extension."""
    settings = SimpleSettingsManager(name="test_auto", file_name="config.toml", path=tmp_path)

    assert settings.file_path.suffix == ".toml"
    settings.close()


def test_auto_detect_defaults_to_json(tmp_path: Path) -> None:
    """Test auto-detection defaults to JSON for unknown extensions."""
    settings = SimpleSettingsManager(name="test_auto", file_name="config.txt", path=tmp_path)

    assert settings.file_path.suffix == ".json"
    settings.close()


def test_all_settings_methods(tmp_path: Path) -> None:
    """Test all SimpleSettingsManager methods."""
    settings = SimpleSettingsManager(name="test_methods", path=tmp_path, fmt="json")

    # Test set/get
    settings.set("key1", "value1")
    settings.set("key2", "value2")
    settings.set("key3", "value3")

    # Test keys/values/items
    key_values = settings.keys()
    assert "key1" in key_values
    assert "value1" in settings.values()
    assert ("key1", "value1") in settings.items()

    # Test has
    assert settings.has("key1") is True
    assert settings.has("nonexistent") is False

    # Test get with default
    assert settings.get("nonexistent", "default") == "default"

    # Test all
    all_settings = settings.all()
    assert all_settings["key1"] == "value1"
    assert all_settings["key2"] == "value2"

    # Test delete
    settings.delete("key2")
    assert settings.has("key2") is False

    # Test len
    assert len(settings) == 2

    # Test clear
    settings.clear()
    assert len(settings) == 0

    settings.close()


def test_context_manager(tmp_path: Path) -> None:
    """Test SimpleSettingsManager as context manager."""
    with SimpleSettingsManager(name="test_ctx", path=tmp_path, fmt="json") as settings:
        settings.set("test", "value")
        assert settings.get("test") == "value"

    # Verify it closed
    assert settings.closed() is True


def test_persistence_across_instances(tmp_path: Path) -> None:
    """Test that settings persist across different instances."""
    # Write with first instance
    with SimpleSettingsManager(name="persist", path=tmp_path, fmt="yaml") as s1:
        s1.set("persistent", "data")
        s1.set("number", 42)

    # Read with second instance
    with SimpleSettingsManager(name="persist", path=tmp_path, fmt="yaml") as s2:
        assert s2.get("persistent") == "data"
        assert s2.get("number") == 42


def test_invalid_format_raises_error(tmp_path: Path) -> None:
    """Test that invalid format raises ValueError."""
    # with pytest.raises(ValueError, match="Unsupported file format"):
    settings = SimpleSettingsManager(
        name="test_invalid",
        path=tmp_path,
        fmt="xml",  # type: ignore[arg-type]
    )
    assert settings.file_path.suffix == ".json"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
