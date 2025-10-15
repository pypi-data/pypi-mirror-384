"""JSON file handler built on top of TextFileHandler.

This handler is intentionally format-agnostic at the IO layer. It exposes
read_text/write_text for JSON storage to perform serialization separately.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, overload

from bear_dereth.files.text.file_handler import TextFileHandler
from bear_dereth.lazy_imports import lazy
from bear_dereth.typing_tools import JSONLike, LitFalse, LitTrue

json: ModuleType = lazy("json")

if TYPE_CHECKING:
    from pathlib import Path
    from types import ModuleType


class JSONFileHandler(TextFileHandler):
    """Thin subclass for semantic clarity (JSON full-text IO)."""

    def __init__(self, file: str | Path, mode: str = "r+", encoding: str = "utf-8") -> None:
        """Initialize the JSON file handler."""
        super().__init__(file=file, mode=mode, encoding=encoding)

    def write(self, data: Any, **kwargs) -> None:
        """Write a Python object as JSON to the file."""
        if isinstance(data, (dict | list)):
            string: str = json.dumps(data, **kwargs)
        else:
            string = str(data)
        super().write(string)

    @overload
    def read(self, as_json: LitTrue = True) -> JSONLike: ...

    @overload
    def read(self, as_json: LitFalse) -> str: ...

    def read(self, as_json: bool = True, **kwargs) -> str | JSONLike:  # type: ignore[override]
        """Read the raw text content of the file or parse as JSON if specified."""
        string: str = super().read()
        if string and as_json:
            return json.loads(string, **kwargs)
        return string

    def to_string(self, **kwargs) -> str:
        """Return the raw text content of the file."""
        string: str = self.read(as_json=False)
        return json.dumps(json.loads(string), **kwargs) if string else ""

    def to_json(self) -> JSONLike | None:
        """Return the JSON content of the file as a Python object."""
        value: JSONLike = self.read(as_json=True)
        return value if isinstance(value, JSONLike) else None


__all__ = ["JSONFileHandler"]
