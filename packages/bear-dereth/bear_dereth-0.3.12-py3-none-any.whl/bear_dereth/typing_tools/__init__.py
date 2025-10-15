"""A set of type aliases and utility functions for type validation and inspection."""

from collections.abc import Callable
from typing import Any, Literal, NoReturn

from .builtin_tools import check_for_conflicts
from .from_type import type_to_str
from .infer import infer_inner_type, infer_type, str_to_bool
from .to_type import coerce_to_type, mapping_to_type, str_to_type, value_to_type
from .type_helper import TypeHelper, num_type_params, type_param, validate_type
from .utils import ArrayLike, JSONLike, TypeHint, a_or_b, is_array_like, is_json_like, is_mapping, is_object

LitInt = Literal["int"]
LitFloat = Literal["float"]
LitStr = Literal["str"]
LitBool = Literal["bool"]
LitList = Literal["list"]
LitDict = Literal["dict"]
LitTuple = Literal["tuple"]
LitSet = Literal["set"]
LitPath = Literal["path"]
LitBytes = Literal["bytes"]

LitFalse = Literal[False]
LitTrue = Literal[True]

OptInt = int | None
OptFloat = float | None
OptStr = str | None
OptBool = bool | None
OptStrList = list[str] | None
OptStrDict = dict[str, str] | None

NoReturnCall = Callable[..., NoReturn]


def format_default_value(value: Any) -> str:
    """Format a default value for string representation in code.

    Args:
        value (Any): The value to format.

    Returns:
        str: The formatted string representation of the value.
    """
    if isinstance(value, str):
        return f'"{value}"'
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int | float)):
        return str(value)
    return repr(value)


__all__ = [
    "ArrayLike",
    "JSONLike",
    "LitBool",
    "LitFalse",
    "LitFloat",
    "LitInt",
    "LitStr",
    "LitTrue",
    "NoReturnCall",
    "OptBool",
    "OptFloat",
    "OptInt",
    "OptStr",
    "OptStrDict",
    "OptStrList",
    "TypeHelper",
    "TypeHint",
    "a_or_b",
    "check_for_conflicts",
    "coerce_to_type",
    "format_default_value",
    "infer_inner_type",
    "infer_type",
    "is_array_like",
    "is_json_like",
    "is_mapping",
    "is_object",
    "mapping_to_type",
    "num_type_params",
    "str_to_bool",
    "str_to_type",
    "type_param",
    "type_to_str",
    "validate_type",
    "value_to_type",
]
