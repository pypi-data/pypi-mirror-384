"""Utility functions for dictionary operations."""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import TYPE_CHECKING, Any, Literal

from bear_dereth.operations.common import KeyCounts, find_new_key
from bear_dereth.operations.factories import inject_tools

if TYPE_CHECKING:
    from collections.abc import Callable

ConflictResolutionChoice = Literal["error", "skip_last", "skip_first", "add_number"]


def dict_verify(*dicts: dict[Any, Any]) -> None:
    """Verify that all arguments are dictionaries.

    Args:
        *dicts (dict): Dictionaries to verify.

    Raises:
        TypeError: If any argument is not a dictionary.
    """
    from bear_dereth.typing_tools import all_same_type  # noqa: PLC0415

    if not all_same_type(dicts, MutableMapping):
        raise TypeError("All arguments must be dictionaries (MutableMapping)")


@inject_tools(default_factory="dict")
def basic_merge[T](*dicts: dict[Any, T], factory: Callable[..., dict[Any, T]]) -> dict[Any, T]:
    """Merge multiple dictionaries into one.

    Args:
        *dicts (dict): Dictionaries to merge.
        **kwargs: Optional keyword arguments.
            - factory (Callable): A callable that returns a new dictionary instance. Defaults to dict.

    Returns:
        dict: Merged dictionary.
    """
    dict_verify(*dicts)
    result: dict[Any, T] = factory()
    for d in dicts:
        result.update(d)
    return result


def key_counts(*d: dict[Any, Any]) -> KeyCounts:
    """Count occurrences of each key across multiple dictionaries, delinating the different dictionaries.

    Args:
        *d (dict): Dictionaries to count keys from.

    Returns:
        dict: A dictionary mapping each key to its occurrence count.

    Example:
        >>> key_counts({"a": 1, "b": 2}, {"b": 3, "c": 4})
        {'a': 1, 'b': 2, 'c': 1}
    """
    dict_verify(*d)
    counts = KeyCounts()
    for dictionary in d:
        for index, key in enumerate(dictionary):
            counts.plus(key, index, dictionary)
    return counts


def update_keys(d: dict[Any, Any], key_map: dict[Any, Any]) -> dict[Any, Any]:
    """Update keys in a dictionary based on a provided mapping.

    Args:
        d (dict): The original dictionary.
        key_map (dict): A mapping of old keys to new keys.

    Returns:
        dict: A new dictionary with updated keys.

    Example:
        >>> update_keys({"a": 1, "b": 2}, {"a": "alpha", "b": "beta"})
        {'alpha': 1, 'beta': 2}
    """
    dict_verify(d, key_map)
    return {key_map.get(k, k): v for k, v in d.items()}


@inject_tools(default_factory="dict")
def merge[T](
    *dicts: dict[Any, T],
    factory: Callable[..., dict[Any, T]],
    overwrite_keys: bool = True,
    conflict_choice: ConflictResolutionChoice = "error",
) -> dict[Any, T]:
    """Combine two dictionaries into one.

    Args:
        *dicts (dict[Any, T]): Dictionaries to combine.
        overwrite_keys (bool): If True, values from later dictionaries will overwrite those from earlier ones for duplicate keys. Defaults to True.
        conflict_choice (ConflictResolutionChoice): Strategy for handling key conflicts when overwrite_keys is False.
            - "error": Raise a ValueError on key conflict.
            - "skip_last": Keep the first occurrence, skip subsequent ones.
            - "skip_first": Keep the last occurrence, skip previous ones.
            - "add_number": Append a number to the key to make it unique (e.g., "key", "key_1", "key_2", etc.).

    Returns:
        dict[Any, T]: A new dictionary containing all items from both input dictionaries.

    Example:
        >>> combine_dicts({"a": 1, "b": 2}, {"b": 3, "c": 4})
        {'a': 1, 'b': 3, 'c': 4}
    """
    dict_verify(*dicts)
    if overwrite_keys:
        return basic_merge(*dicts)

    all_keys: list[Any] = [k for d in dicts for k in d]
    dupes: set[tuple[int, Any]] = {(i, k) for i, d in enumerate(dicts) for k in d if all_keys.count(k) > 1}
    match conflict_choice:
        case "error":
            if dupes:
                raise ValueError(f"Key conflict detected for keys: {', '.join(str(k) for _, k in dupes)}")
        case "skip_last":
            return basic_merge(*reversed(dicts))
        case "skip_first":
            return basic_merge(*dicts)
        case "add_number":
            result: dict[Any, T] = factory()
            counts: KeyCounts = key_counts(*dicts)
            for d in dicts:
                for k, v in d.items():
                    # TODO: We are basically forcing str keys here, probably not a better way to do this
                    # I'd imagine this is a rare use case anyway
                    key: Any = k if not counts.is_dupe(k) else find_new_key(k, set(result.keys()))
                    result[key] = v
            return result
        case _:
            ...
    raise ValueError(f"Invalid conflict resolution choice: {conflict_choice}")
