"""Tools related to string manipulation."""

from .flatten_data import FlattenPower, flatten
from .manipulation import (
    CaseConverter,
    detect_case,
    slugify,
    to_camel,
    to_kebab,
    to_pascal,
    to_screaming_snake,
    to_snake,
    truncate,
)


def to_lines(raw: str) -> list[str]:
    """Return a list of non-empty, stripped lines from the raw data.

    Args:
        raw: The raw string data to be processed.

    Returns:
        A list of non-empty, stripped lines.
    """
    return [line for line in raw.strip().splitlines() if line.strip()]


__all__ = [
    "CaseConverter",
    "FlattenPower",
    "detect_case",
    "flatten",
    "slugify",
    "to_camel",
    "to_kebab",
    "to_lines",
    "to_pascal",
    "to_screaming_snake",
    "to_snake",
    "truncate",
]
