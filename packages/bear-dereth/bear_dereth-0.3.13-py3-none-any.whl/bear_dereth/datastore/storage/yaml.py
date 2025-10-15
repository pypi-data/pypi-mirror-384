"""YAML storage backend for the datastore.

Provides YAML file storage using the unified data format.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bear_dereth.datastore.unified_data import UnifiedDataFormat
from bear_dereth.files.helpers import touch
from bear_dereth.files.yaml.file_handler import YamlFileHandler

from .base_storage import Storage

if TYPE_CHECKING:
    from pathlib import Path


class YamlStorage(Storage):
    """A YAML file storage backend using the unified data format."""

    def __init__(self, file: str | Path, file_mode: str = "r+", encoding: str = "utf-8") -> None:  # noqa: ARG002
        """Initialize YAML storage.

        Args:
            file: Path to the YAML file
            file_mode: File mode (unused, kept for API consistency)
            encoding: Text encoding to use (default: "utf-8")
        """
        super().__init__()
        self.file: Path = touch(file, mkdir=True)
        self.handler = YamlFileHandler(self.file, encoding=encoding)

    def read(self) -> UnifiedDataFormat | None:
        """Read data from YAML file.

        Returns:
            UnifiedDataFormat instance or empty if file doesn't exist.
        """
        try:
            model: UnifiedDataFormat = UnifiedDataFormat.model_validate(self.handler.read())
            return model
        except Exception:
            return None

    def write(self, data: UnifiedDataFormat) -> None:
        """Write data to YAML file with pretty formatting.

        Args:
            data: UnifiedDataFormat instance to write.
        """
        yaml_data: dict = data.model_dump(exclude_none=True)
        self.handler.write(yaml_data)

    def close(self) -> None:
        """Close the file handle (no-op for YAML handler)."""
        if self.closed:
            return
        # YAML handler doesn't maintain open file handles

    @property
    def closed(self) -> bool:
        """Check if the storage is closed (always returns False for YAML)."""
        return False


__all__ = ["YamlStorage"]
