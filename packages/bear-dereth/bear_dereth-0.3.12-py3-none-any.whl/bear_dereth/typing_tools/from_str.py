"""Convert string representations of types to actual Python types in various ways."""

from typing import Literal, overload

POSSIBLE_BOOL_STRINGS: set[str] = {"true", "false", "1", "0", "yes", "no"}


@overload
def str_to_bool(val: str, as_str: Literal[True]) -> str: ...


@overload
def str_to_bool(val: str, as_str: Literal[False] = False) -> bool: ...


def str_to_bool(val: str, as_str: bool = False) -> bool | str:
    """Check if a string represents a boolean value, either returning a bool or the string "bool".

    Returns:
        bool: The boolean value.
    """
    if as_str and str(val).strip().lower() in POSSIBLE_BOOL_STRINGS:
        return "bool"

    return str(val).strip().lower() in {"true", "1", "yes"}
