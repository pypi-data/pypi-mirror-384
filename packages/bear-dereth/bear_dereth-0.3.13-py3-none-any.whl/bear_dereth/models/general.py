"""A set of general-purpose Pydantic models and utilities."""

from pydantic import BaseModel, ConfigDict


class FrozenModel(BaseModel):
    """A Pydantic model that is immutable after creation."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class ExtraIgnoreModel(BaseModel):
    """A Pydantic model that ignores extra fields."""

    model_config = ConfigDict(extra="ignore")
