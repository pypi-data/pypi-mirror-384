"""YAML file handler for Bear Dereth."""

from __future__ import annotations

from typing import IO, TYPE_CHECKING, Any, Self

from pydantic import BaseModel
import yaml

from bear_dereth.files.base_file_handler import BaseFileHandler
from bear_dereth.files.file_lock import FileLock

if TYPE_CHECKING:
    from pathlib import Path

YamlData = dict[str, Any]


class YamlConfig(BaseModel):
    safe_mode: bool = True
    default_flow_style: bool = False
    sort_keys: bool = False
    indent: int = 2
    width: int | None = None
    allow_unicode: bool = True


class YamlFileHandler(BaseFileHandler[YamlData]):
    """YAML file handler with safe defaults and formatting options."""

    def __init__(
        self,
        file: Path | str,
        encoding: str = "utf-8",
        safe_mode: bool = True,
        flow_style: bool = False,
        sort_keys: bool = False,
        indent: int = 2,
        width: int | None = None,
    ) -> None:
        """Initialize the YAML file handler.

        Args:
            path: Path to the YAML file
            encoding: File encoding (default: "utf-8")
            safe_mode: Use safe_load/safe_dump (default: True, recommended)

        Raises:
            ImportError: If PyYAML is not installed
        """
        super().__init__(file, mode="r+", encoding=encoding)
        self.opts = YamlConfig(
            safe_mode=safe_mode,
            default_flow_style=flow_style,
            sort_keys=sort_keys,
            indent=indent,
            width=width,
        )
        self.options: dict[str, Any] = self.opts.model_dump(exclude={"safe_mode"})

    def read(self, **_) -> dict[str, Any]:
        """Read and parse YAML file.

        Returns:
            Parsed YAML data as dictionary

        Raises:
            yaml.YAMLError: If file contains invalid YAML
            ValueError: If file cannot be read
        """
        handle: IO[Any] | None = self.handle()
        if handle is None:
            raise ValueError("File handle is not available.")
        with FileLock(handle):
            handle.seek(0)
            if self.opts.safe_mode:
                data: YamlData = yaml.safe_load(handle)
            else:
                data = yaml.load(handle, Loader=yaml.FullLoader)  # noqa: S506
            return data or {}

    def write(self, data: YamlData, **kwargs) -> None:
        """Write data as YAML to file.

        Args:
            data: Data to serialize as YAML (must be dict-like)

        Raises:
            yaml.YAMLError: If data cannot be YAML serialized
            ValueError: If file cannot be written
        """
        handle: IO[Any] | None = self.handle()
        if handle is None:
            raise ValueError("File handle is not available.")
        with FileLock(handle):
            try:
                handle.seek(0)
                handle.truncate(0)
                options: dict[str, Any] = self.options.copy()
                options.update(kwargs)
                if self.opts.safe_mode:
                    yaml.safe_dump(data, handle, **options)
                else:
                    yaml.dump(data, handle, **options)
            except yaml.YAMLError as e:
                raise ValueError(f"Cannot serialize data to YAML: {e}") from e
            except Exception as e:
                raise ValueError(f"Error writing YAML file {self.file}: {e}") from e

    def to_string(self, data: YamlData | None = None, **kwargs) -> str:
        """Convert data to YAML string without writing to file.

        Args:
            data: Data to serialize (uses cached data if None)

        Returns:
            YAML formatted string

        Raises:
            ValueError: If data cannot be serialized
        """
        to_serialize: YamlData = data if data is not None else self.read()
        options: dict[str, Any] = self.options.copy()
        options.update(kwargs)
        try:
            if self.opts.safe_mode:
                return yaml.safe_dump(to_serialize, **options)
            return yaml.dump(to_serialize, **options)
        except yaml.YAMLError as e:
            raise ValueError(f"Cannot serialize data to YAML: {e}") from e

    def __enter__(self) -> Self:
        """Enter context manager."""
        self.read()
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        """Exit context manager."""
        self.close()


__all__ = ["YamlData", "YamlFileHandler"]
