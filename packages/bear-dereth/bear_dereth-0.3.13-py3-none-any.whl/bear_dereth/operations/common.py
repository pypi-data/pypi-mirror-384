"""Common tools for operations in Bear Dereth project."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Literal, NamedTuple, ParamSpec, Self, TypeVar

CollectionChoice = Literal["list", "set", "dict", "defaultdict"]

Return = TypeVar("Return")
P = ParamSpec("P")

ReturnedCallable = Callable[..., dict | list | set | Callable]

PARAM_NAMES: set[str] = {"container", "ctx", "accessor", "transformer"}
PARAM_OPS: set[str] = {"getter", "setter", "deleter"}


def default_factory(**kwargs) -> ReturnedCallable:
    """Default factory function to create collections based on choice."""
    choice: CollectionChoice = kwargs.pop("choice", "dict")
    if factory := kwargs.pop("override", False):
        return factory
    match choice:
        case "list":
            return list
        case "set":
            return set
        case "dict":
            return dict
        case "defaultdict":
            return defaultdict
        case _:
            raise ValueError(f"Invalid choice: {choice}")


class Location(NamedTuple):
    """Structure to hold location information."""

    i: int
    instance_id: int


@dataclass
class Counts:
    """Structure to hold dictionary keys information."""

    key: Any
    instance_ids: list[Location] = field(default_factory=list)

    @property
    def count(self) -> int:
        """Number of occurrences of the key."""
        return len(self.instance_ids)


@dataclass
class KeyCounts:
    """Structure to hold key counts and duplicates information."""

    _counts: dict[Any, Counts] = field(default_factory=dict)

    def is_dupe(self, key: Any) -> bool:
        """Check if a key is a duplicate."""
        return key in self.dupes

    @cached_property
    def dupes(self) -> set[Any]:
        """Set of duplicate keys across different instance IDs."""
        return {key for key, counts in self.counts.items() if counts.count > 1}

    @property
    def counts(self) -> dict[Any, Counts]:
        """Dictionary of key counts."""
        return dict(sorted(self._counts.items(), key=lambda item: (-item[1].count, item[0])))

    def plus(self, key: Any, index: int, instance_id: object) -> Self:
        """Add a key occurrence for a specific instance ID."""
        instance_id = id(instance_id)
        if key not in self.counts:
            self._counts[key] = Counts(key)
        self._counts[key].instance_ids.append(Location(i=index, instance_id=instance_id))
        return self

    def to_dict(self) -> dict[Any, dict[str, Any]]:
        """Convert KeyCounts to a dictionary representation."""
        return {
            key: {
                "count": counts.count,
                "instances": [(loc.i, loc.instance_id) for loc in counts.instance_ids],
            }
            for key, counts in self.counts.items()
        }

    def __str__(self) -> str:
        """String representation of the KeyCounts."""
        result = "KeyCounts:\n"
        for key, counts in self.counts.items():
            result += f"  Key: {key}, Count: {counts.count}, Instances: {[(loc.i, loc.instance_id) for loc in counts.instance_ids]}\n"
        return result

    def __repr__(self) -> str:
        """Official string representation of the KeyCounts."""
        return f"KeyCounts(counts={self.counts}, dupes={self.dupes})"


def find_new_key(key: Any, existing: set[Any], suffix: int = 1, limit: int = 5) -> Any:
    """Find a new key by appending a suffix if the key already exists.

    Args:
        key (Any): The original key.
        existing (set): A set of existing keys to check against.
        suffix (int): The starting suffix to append. Defaults to 1.
        limit (int): The maximum number of attempts to find a new key. Defaults to 5.


    Returns:
        Any: A new key that does not exist in the existing set.
    """
    base_k: Any = key
    while key in existing:
        if suffix > limit:
            raise ValueError(f"Could not find a new key for '{base_k}' after {limit} attempts.")
        key = f"{base_k}_{suffix}"
        suffix += 1
    return key
