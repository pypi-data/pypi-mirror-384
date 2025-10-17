"""A module defining the Columns model for representing table columns."""

from __future__ import annotations

from contextlib import suppress
import re
from typing import Any

from pydantic import Field, field_validator

from bear_dereth.models.general import ExtraIgnoreModel


class Columns[T](ExtraIgnoreModel):
    """A model to represent columns in a table."""

    name: str = ""
    type: str = Field(default=type[T].__name__ or "str")
    default: Any = None
    nullable: bool = False
    primary_key: bool | None = None
    auto_increment: bool | None = None

    @field_validator("type", mode="before")
    @classmethod
    def validate_type(cls, v: Any) -> str:
        """Ensure the type is stored as a string."""
        if isinstance(v, type):
            return v.__name__
        if isinstance(v, str):
            with suppress(Exception):
                # 'Columns[str]' -> 'str'
                v = re.sub(r"^Columns\[(.+)\]$", r"\1", v)
            return v
        raise TypeError("Type must be a string or a type.")

    @property
    def is_int(self) -> bool:
        """Check if the column type is integer."""
        return self.type.lower() in {"int", "integer"}

    def __hash__(self) -> int:
        """Hash the column based on its attributes."""
        return hash((self.name, self.type, self.nullable, self.primary_key))

    def render(self) -> dict[str, Any]:
        """Render the column as a dictionary."""
        return self.model_dump(exclude_none=True)

    def items(self) -> list[tuple[str, Any]]:
        """Return items for the column."""
        return list(self.render().items())


NullColumn: Columns[None] = Columns(name="NULL", type="null", nullable=True, default=None)
