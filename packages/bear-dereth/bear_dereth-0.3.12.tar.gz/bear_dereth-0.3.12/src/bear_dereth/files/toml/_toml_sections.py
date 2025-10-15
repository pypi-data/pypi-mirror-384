"""A helper class for TOML sections for dot notation parsing."""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any, Self

from bear_dereth.data_structs.stacks import SimpleStack as Stack

if TYPE_CHECKING:
    from bear_dereth.files.toml.file_handler import TomlData


class TomlSection:
    """Fluent accessor for TOML data with dot notation."""

    def __init__(self, data: TomlData) -> None:
        """Initialize with the full TOML data."""
        self._data = data
        self._path: list[str] = []

    def _set_path(self, path: list[str], key: str) -> Self:
        """Set the current path."""
        self._path = [*path, key]
        return self

    @cached_property
    def dot_map(self) -> dict[str, Any]:
        """Map out all possible paths for fast lookup."""
        result: dict[str, Any] = {}
        stack: Stack[tuple[list, TomlData]] = Stack(([], self._data))

        while stack:
            current_path, current_value = stack.pop()
            if isinstance(current_value, dict):
                for k, v in current_value.items():
                    stack.push(([*current_path, k], v))
            else:
                result[".".join(current_path)] = current_value
        return result

    def _navigate(self) -> TomlData | None:
        """Walk the current path."""
        return self.dot_map.get(".".join(self._path))

    def __getattr__(self, key: str) -> TomlSection:
        """Access a sub-key, returning a new TomlSection."""
        return TomlSection(self._data)._set_path(self._path, key)

    def get(self, default: Any = None) -> TomlData | None:
        """Resolve the path and return value."""
        result: TomlData | None = self._navigate()
        return result if result is not None else default


if __name__ == "__main__":
    sample_toml: str = """
    [project]
    name = "bear-dereth"
    description = "A set of common tools for various bear projects."
    dynamic = ["version"]
    authors = [{name = "chaz", email = "bright.lid5647@fastmail.com"}]
    readme = "README.md"
    requires-python = ">=3.12"
    keywords = []
    dependencies = [
        "bear-epoch-time>=1.2.2",
        "distro>=1.9.0",
        "pydantic>=2.11.5",
        "pyyaml>=6.0.3",
        "rich>=14.1.0",
        "singleton-base>=1.2.3",
        "tomlkit>=0.13.3",
    ]

    [project.scripts]
    bear-dereth = "bear_dereth._internal.cli:main"

    [build-system]
    requires = ["hatchling", "uv-dynamic-versioning"]
    build-backend = "hatchling.build"
    """
    from tomllib import loads

    parsed_data: TomlData = loads(sample_toml)
    toml_section: TomlSection = TomlSection(data=parsed_data)

    print(toml_section.project.name)  # Outputs: bear-dereth
    print(toml_section.dot_map)
