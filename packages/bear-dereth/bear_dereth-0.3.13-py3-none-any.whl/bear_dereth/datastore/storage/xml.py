"""XML storage backend for the datastore.

Provides self-describing XML file storage with type annotations and validation metadata.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bear_dereth.datastore.adapter.xml import XMLDeserializer, XMLSeralizer
from bear_dereth.files.helpers import touch
from bear_dereth.files.xml import XMLFilehandler

from .base_storage import Storage

if TYPE_CHECKING:
    from pathlib import Path

    from bear_dereth.datastore.unified_data import UnifiedDataFormat


class XMLStorage(Storage):
    """An XML file storage backend using self-describing XML format.

    This implementation produces highly self-documenting XML with explicit type
    annotations, counts for validation, and metadata attributes referencing the
    Pydantic models. This enables robust parsing and validation without external
    schema knowledge.
    """

    def __init__(self, file: str | Path, file_mode: str = "r+", encoding: str = "utf-8") -> None:
        """Initialize XML storage.

        Args:
            file: Path to the XML file
            file_mode: File mode for opening (default: "r+" for read/write)
            encoding: Text encoding to use (default: "utf-8")
        """
        super().__init__()
        self.file: Path = touch(file, mkdir=True)
        self.handler = XMLFilehandler(self.file, mode=file_mode, encoding=encoding)

    def read(self) -> UnifiedDataFormat | None:
        """Read data from XML file.

        Returns:
            UnifiedDataFormat instance populated from the XML file.
        """
        try:
            with XMLDeserializer(self.handler.read().getroot()) as deserializer:
                return deserializer.to_data()
        except Exception:
            return None

    def write(self, data: UnifiedDataFormat, pretty: bool = True) -> None:
        """Write data to XML file in idiomatic XML format.

        Args:
            data: UnifiedDataFormat instance to write.
            pretty: Whether to pretty-print the XML (default: True)
        """
        with XMLSeralizer(data) as serializer:
            self.handler.write(serializer.to_tree(), pretty=pretty)

    def close(self) -> None:
        """Close the file handle."""
        if self.closed:
            return
        self.handler.close()

    @property
    def closed(self) -> bool:
        """Check if the storage is closed."""
        return self.handler.closed
