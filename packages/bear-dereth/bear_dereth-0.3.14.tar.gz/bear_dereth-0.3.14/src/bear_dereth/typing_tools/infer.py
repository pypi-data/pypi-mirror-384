"""Utilities for inferring types of Python values."""

from collections.abc import Callable
from contextlib import suppress
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import Any, Literal, overload
from warnings import deprecated

from bear_dereth.data_structs.freezing import freeze
from bear_dereth.lazy_imports import lazy
from bear_dereth.operations import always_true, if_in_list, if_is_instance
from bear_dereth.sentinels import CONTINUE
from bear_dereth.typing_tools.builtin_tools import type_name
from bear_dereth.typing_tools.from_type import PossibleStrs, type_to_str

ast: ModuleType = lazy("ast")

ACCEPTABLE_TYPE_STRS: set[str] = {"int", "float", "bool", "bytes", "list", "dict", "tuple", "set", "NoneType"}
ACCEPTABLE_TYPES: tuple[type, ...] = (int, float, bool, list, dict, tuple, set, bytes)
COLLECTION_TYPES: tuple[str, ...] = ("list", "dict", "tuple", "set")


def type_brackets(t: str, s: str) -> str:
    """Helper to format type strings."""
    return f"{t}[{s}]"


def eval_to_type_str(
    value: Any,
    cond: Callable[..., bool] | None = None,
    *args,
    **kwargs,
) -> PossibleStrs | Any:
    """Uses ast.literal_eval to convert a string wrapped value to its native type and then to its string type.

    Args:
        value (Any): The value to convert.
        cond (Callable[[PossibleStrs], bool]): A callable that takes a PossibleStrs and returns a bool
    Returns:
        PossibleStrs | Any: The converted value as PossibleStrs if successful and condition is met, otherwise CONTINUE.
    """
    if cond is None:
        cond = always_true
    if isinstance(value, str):
        try:
            v: PossibleStrs = type_to_str(type(ast.literal_eval(value)))
            return v if cond(v, *args, **kwargs) else CONTINUE
        except (TypeError, ValueError, SyntaxError):
            return CONTINUE
    else:
        return type_to_str(type(value))


@lru_cache(maxsize=128)
def eval_to_native(
    v: Any,
    cond: Callable[..., bool] | None = None,
    *args,
    **kwargs,
) -> Any:
    """Uses ast.literal_eval to convert a string wrapped value to its native typ or string type.

    Args:
        value (Any): The value to convert.
        cond (Callable[[Any], bool]): A callable that takes a value and returns a bool, determining if the conversion is acceptable.
            If None, any successful conversion is accepted.
        args: Additional positional arguments to pass to the condition callable.
        kwargs: Additional keyword arguments to pass to the condition callable.

    Returns:
        Any: The converted value if successful and condition is met, otherwise the original value.
    """
    if cond is None:
        cond = always_true

    with suppress(Exception):
        evaluated: Any = ast.literal_eval(v)
        if cond(evaluated, *args, **kwargs):
            return evaluated
    return CONTINUE


@lru_cache(maxsize=128)
def is_collection_type(value: Any) -> bool:
    """Check if a value is a collection type (list, tuple, set, dict)."""
    return value in COLLECTION_TYPES


def path_check(value: str, path_as_str: bool) -> bool:
    """Check if a string represents a valid filesystem path."""
    with suppress(Exception):
        if not path_as_str:
            return Path(value).exists()
    return False


@lru_cache(maxsize=128)
def str_type(value: str) -> str:
    """Infer the type of a str wrapped value and return it as a string.

    Args:
        value(str): The value to infer the type of that is wrapped in a str.

    Returns:
        A string representing the inferred type.
    """
    string_value: PossibleStrs = eval_to_type_str(value, if_in_list, lst=freeze(ACCEPTABLE_TYPE_STRS))
    if string_value is not CONTINUE:
        return string_value
    if isinstance(value, str):
        return "str"
    return "Any"  # Should basically never get here


class Inference:
    """Class to find the inner type of array-like structures."""

    def __init__(
        self,
        value: Any | None = None,
        path_as_str: bool = False,
        arb_types_allowed: bool = False,
    ) -> None:
        """Initialize with a value to infer its type."""
        self._value: Any | None = value
        self.path_as_str: bool = path_as_str
        self.arb_types_allowed: bool = arb_types_allowed

    def infer_type(self, v: Any | None = None, prime_types_only: bool = False) -> str:
        """Infer the type of the value and return it as a string."""
        if v is not None:
            self.value = v
        value: str = self._infer_type(prime_types_only=prime_types_only)
        self.reset()
        return value

    def _infer_type(self, prime_types_only: bool = False) -> str:
        """Infer the inner type of an array-like structure (list, tuple, set)."""
        if isinstance(self.value, str):
            value: Any = eval_to_native(self.value, if_is_instance, types=ACCEPTABLE_TYPES)
            if str_to_bool(self.value, as_str=True) == "bool":
                return "bool"
            if path_check(self.value, self.path_as_str):
                return "path"
            if value is CONTINUE:
                return str_type(self.value)
            self.value = value
        if self.empty_collection:
            return type_to_str(type(self.value))
        if isinstance(self.value, tuple):
            return self._tuple_work(self.value, prime_types_only=prime_types_only)
        if isinstance(self.value, list):
            return self._general_work("list", prime_types_only=prime_types_only)
        if isinstance(self.value, set):
            return self._general_work("set", prime_types_only=prime_types_only)
        if isinstance(self.value, dict):
            return self._dict_work(self.value, prime_types_only=prime_types_only)
        try:
            return type_to_str(type(self.value))
        except Exception:
            return "Any"  # Should basically never get here

    def _dict_work(self, type_str: Any, prime_types_only: bool = False) -> str:
        """Handle special cases for dicts."""
        if prime_types_only:
            return "dict"
        dict_key: set[str] = {type_name(k) for k in type_str}
        key_type: str = type_name(next(iter(type_str))) if len(dict_key) == 1 else "Any"
        if self.all_types_are_same:
            return type_brackets("dict", f"{key_type}, {self.first_value}")
        return type_brackets("dict", f"{key_type}, {' | '.join(sorted(self.all_value_types))}")

    def _general_work(self, type_str: str, prime_types_only: bool = False) -> str:
        """Handle special cases for sets."""
        if prime_types_only:
            return type_str
        if self.all_types_are_same:
            return type_brackets(type_str, f"{self.first_value}")
        if len(self.all_value_types) == 1:
            return type_brackets(type_str, next(iter(self.all_value_types)))
        return type_brackets(type_str, " | ".join(sorted(self.all_value_types)))

    def _tuple_work(self, value: Any, prime_types_only: bool = False) -> str:
        """Handle special cases for tuples."""
        if prime_types_only:
            return "tuple"
        if not value or (len(self) == 1 and value == ...):
            return type_brackets("tuple", "Any")
        if self.all_types_are_same:
            return type_brackets("tuple", f"{self.first_value}, ...")
        if len(self.all_value_types) == 1:
            return type_brackets("tuple", next(iter(self.all_value_types)))
        return type_brackets("tuple", ", ".join(sorted(self.all_value_types)))

    def reset(self) -> None:
        """Reset the stored value to None."""
        self._value = None

    @property
    def value(self) -> Any:
        """Get the current value."""
        if self._value is None:
            raise ValueError("Value has already been consumed.")
        return self._value

    @value.setter
    def value(self, new_value: Any | None) -> None:
        """Set a new value."""
        self._value = new_value

    @property
    def is_collection(self) -> bool:
        """Check if the outer type is a container type (list, tuple, set)."""
        return is_collection_type(type_to_str(type(self.value), arb_types_allowed=self.arb_types_allowed))

    @property
    def empty_collection(self) -> bool:
        """Check if the value is an empty collection."""
        return self.is_collection and not bool(self.value)

    @property
    def first_value(self) -> str:
        """Get the first value of the collection, or None if not applicable."""
        if not self.is_collection or self.empty_collection:
            return "NoneType"
        return str_type(next(iter(self.value.values())) if isinstance(self.value, dict) else next(iter(self.value)))

    @property
    def all_value_types(self) -> set[str]:
        """Get a set of all unique types in the collection."""
        if not self.is_collection or self.empty_collection:
            return set()
        if not isinstance(self.value, dict):
            return {str_type(i) for i in self.value}
        return {str_type(v) for v in self.value.values()}

    @property
    def all_types_are_same(self) -> bool:
        """Check if all elements in the collection are of the same type."""
        if not self.is_collection or self.empty_collection:
            return False
        return len(self.all_value_types) == 1

    def __len__(self) -> int:
        """Get the length of the collection if applicable, otherwise 0."""
        return len(self.value) if self.is_collection else 0


@lru_cache(maxsize=128)
def infer_type(
    value: str | Any,
    path_as_str: bool = False,
    arb_types_allowed: bool = False,
    prime_types_only: bool = False,
) -> str:
    """Infer the type of a str wrapped value and return it as a string.

    Args:
        value (str): The value to infer the type of that is wrapped in a str.
        path_as_str (bool): Whether to treat valid filesystem paths as strings. Defaults to False.

    Returns:
        str: A string representing the inferred type.
    """
    return Inference(
        value,
        path_as_str=path_as_str,
        arb_types_allowed=arb_types_allowed,
    ).infer_type(prime_types_only=prime_types_only)


@deprecated("Use infer_type instead")
def infer_inner_type(value: Any) -> str:
    """Deprecated: Infer the inner type of an array-like structure (list, tuple, set).

    Args:
        value (Any): The value to infer the inner type of.

    Returns:
        str: A string representing the inferred inner type.
    """
    return Inference(value).infer_type()


@overload
def str_to_bool(val: str, as_str: Literal[True]) -> str: ...


@overload
def str_to_bool(val: str, as_str: Literal[False] = False) -> bool: ...


@lru_cache(maxsize=128)
def str_to_bool(val: str, as_str: bool = False) -> bool | str:
    """Check if a string represents a boolean value, either returning a bool or the string "bool".

    Returns:
        bool: The boolean value.
    """
    value: Any = eval_to_native(str(val).title(), lambda x: isinstance(x, bool))
    if as_str and value is not CONTINUE:
        return "bool"
    return bool(value is not CONTINUE and value)
