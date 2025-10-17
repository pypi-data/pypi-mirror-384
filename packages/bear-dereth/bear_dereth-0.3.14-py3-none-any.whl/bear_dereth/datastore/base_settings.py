"""Base settings model for Pydantic models used in settings storage."""

from __future__ import annotations

from pydantic import BaseModel
from pydantic.fields import FieldInfo

from bear_dereth.datastore.columns import Columns


class BaseSettingsModel(BaseModel):
    """Pydantic model for settings storage."""

    @classmethod
    def field_keys(cls) -> list[str]:
        """Get the list of field names."""
        return list(cls.model_fields.keys())

    @classmethod
    def field_values(cls) -> list[object]:
        """Get the list of field values."""
        return list(cls.model_fields.values())

    @classmethod
    def fields(cls) -> list[tuple[str, object]]:
        """Get the list of field items as (name, field) tuples."""
        return list(cls.model_fields.items())

    @classmethod
    def get_columns(cls) -> list[Columns]:
        """Get the list of columns for the settings model."""
        columns: list[Columns] = []
        for field in cls.field_values():
            if isinstance(field, FieldInfo) and hasattr(field, "annotation") and issubclass(field.annotation, Columns):  # type: ignore[attr-defined]
                col: Columns = field.default
                if col.type is None and hasattr(field, "annotation") and hasattr(field.annotation, "__args__"):  # type: ignore[attr-defined]
                    args = getattr(field.annotation, "__args__", ())
                    if args and len(args) == 1:
                        col.type = args[0].__name__ if hasattr(args[0], "__name__") else str(args[0])  # type: ignore[attr-defined]
                if not isinstance(col, Columns):
                    continue
                columns.append(col)
        return columns
