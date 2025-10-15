"""Simple settings manager supporting multiple file formats."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Self

from bear_dereth.files.helpers import derive_settings_path as to_path
from bear_dereth.files.json.file_handler import JSONFileHandler
from bear_dereth.files.toml.file_handler import TomlFileHandler
from bear_dereth.files.yaml.file_handler import YamlFileHandler
from bear_dereth.lazy_imports import lazy

json: ModuleType = lazy("json")

if TYPE_CHECKING:
    from types import ModuleType

    from bear_dereth.files.base_file_handler import BaseFileHandler

FileFormat = Literal["json", "yaml", "toml", "default"]
FileFormats: tuple = ("json", "yaml", "toml")


def get_file_handler(fmt: FileFormat, file_path: Path, **kwargs) -> BaseFileHandler[dict[str, Any]]:
    """Get the appropriate file handler for the specified format.

    Args:
        fmt: File format (json, yaml, or toml)
        file_path: Path to the file

    Returns:
        File handler instance for the format

    Raises:
        ValueError: If format is not supported
    """
    handlers: dict[FileFormat, type[BaseFileHandler]] = {
        "json": JSONFileHandler,
        "yaml": YamlFileHandler,
        "toml": TomlFileHandler,
        "default": JSONFileHandler,
    }
    return handlers.get(fmt, JSONFileHandler)(file=file_path, **kwargs)


class SimpleSettingsManager:
    """A simple settings manager supporting multiple file formats.

    Supports JSON, YAML, and TOML formats with automatic format detection
    based on file extension or explicit format parameter.

    Examples:
        # JSON (default)
        settings = SimpleSettingsManager("myapp")

        # YAML
        settings = SimpleSettingsManager("myapp", format="yaml")

        # TOML
        settings = SimpleSettingsManager("myapp", format="toml")

        # Auto-detect from extension
        settings = SimpleSettingsManager("myapp", file_name="config.yaml")
    """

    def __init__(
        self,
        name: str,
        file_name: str | None = None,
        path: Path | str | None = None,
        fmt: FileFormat = "default",
        **kwargs,
    ) -> None:
        """Initialize the SimpleSettingsManager.

        Args:
            name: Settings name (used for default file path)
            file_name: Optional custom file name
            path: Optional custom directory path
            format: File format (json, yaml, toml). Auto-detected from extension if not provided.
            kwargs: Additional arguments passed to the file handler
        """
        fmt = self._fmt_to_ext(file_name, fmt)
        self.file_path: Path = to_path(name, file_name, path, ext=fmt)
        self.handler: BaseFileHandler[dict[str, Any]] = get_file_handler(fmt, self.file_path, **kwargs)
        self.settings: dict[str, Any] = self.read()

    def _fmt_to_ext(self, file_name: str | None, fmt: FileFormat) -> FileFormat:
        """Determine file format from file extension."""
        if file_name is None:
            return fmt if fmt in FileFormats else "json"
        ext: str = Path(file_name).suffix.lower().replace(".", "")
        if fmt == "default":
            if ext in ("yml", "yaml"):
                return "yaml"
            if ext == "toml":
                return "toml"
            return "json"
        return fmt if fmt in FileFormats else "json"

    def read(self) -> dict[str, Any]:
        """Read settings from the file.

        Returns:
            Dictionary of settings
        """
        try:
            data: dict[str, Any] = self.handler.read()
            return data if isinstance(data, dict) else {}
        except (ValueError, FileNotFoundError):
            return {}

    def write(self) -> None:
        """Write settings to the file."""
        self.handler.write(self.settings)

    def keys(self) -> list[str]:
        """Get a list of all setting keys."""
        return list(self.settings.keys())

    def values(self) -> list[Any]:
        """Get a list of all setting values."""
        return list(self.settings.values())

    def items(self) -> list[tuple[str, Any]]:
        """Get a list of all setting key-value pairs."""
        return list(self.settings.items())

    def all(self) -> dict[str, Any]:
        """Get all settings as a dictionary."""
        return self.settings.copy()

    def delete(self, key: str) -> None:
        """Delete a setting key."""
        if key in self.settings:
            del self.settings[key]
            self.write()

    def clear(self) -> None:
        """Clear all settings."""
        self.settings.clear()
        self.write()

    def set(self, key: str, value: Any) -> None:
        """Set a setting value."""
        self.settings[key] = value
        self.write()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self.settings.get(key, default)

    def has(self, key: str) -> bool:
        """Check if a setting key exists."""
        return key in self.settings

    def closed(self) -> bool:
        """Check if the file handle is closed."""
        return self.handler.closed

    def close(self) -> None:
        """Close the file handle."""
        self.handler.close()

    def __del__(self) -> None:
        self.close()

    def __len__(self) -> int:
        return len(self.settings)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self.close()
