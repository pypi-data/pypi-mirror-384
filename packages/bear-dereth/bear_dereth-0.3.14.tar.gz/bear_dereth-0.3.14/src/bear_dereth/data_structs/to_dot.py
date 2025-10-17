"""Provide dot notation access to nested dictionaries."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import MutableMapping
from typing import TYPE_CHECKING, Any, Self

from bear_dereth.data_structs.freezing import freeze
from bear_dereth.lazy_imports import lazy

if TYPE_CHECKING:
    from collections.abc import Iterator

_json = lazy("json")
copy = lazy("copy")


class DotDict(MutableMapping):
    """A dictionary that supports dot notation access to nested dictionaries.

    Example:
        >>> d = DotDict({"a": {"b": {"c": 1}}})
        >>> d.a.b.c
        1
        >>> d["a"]["b"]["c"]
        1
        >>> d.a.b.c = 2
        >>> d.a.b.c
        2
        >>> d["a"]["b"]["c"]
        2
    """

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        """Initialize the DotDict with an optional dictionary."""
        self._data: OrderedDict[str, Any] = OrderedDict()
        for key, value in (data or {}).items():
            if isinstance(value, dict):
                self._data[key] = DotDict(value)
            else:
                self._data[key] = value

    def __getattr__(self, key: str) -> Any:
        """Get an item using dot notation."""
        try:
            value = self._data[key]
            if isinstance(value, dict):
                return DotDict(value)
            return value
        except KeyError as e:
            raise AttributeError(f"'DotDict' object has no attribute '{key}'") from e

    def __setattr__(self, key: str, value: Any) -> None:
        """Set an item using dot notation."""
        if key == "_data":
            super().__setattr__(key, value)
        else:
            self._data[key] = value

    def __delattr__(self, key: str) -> None:
        """Delete an item using dot notation."""
        try:
            del self._data[key]
        except KeyError as e:
            raise AttributeError(f"'DotDict' object has no attribute '{key}'") from e

    def __getitem__(self, key: str) -> Any:
        """Get an item using dictionary notation."""
        value = self._data[key]
        if isinstance(value, dict):
            return DotDict(value)
        return value

    def __setitem__(self, key: str, value: Any) -> None:
        """Set an item using dictionary notation."""
        self._data[key] = value

    def __delitem__(self, key: str) -> None:
        """Delete an item using dictionary notation."""
        del self._data[key]

    def __iter__(self) -> Iterator[str]:
        """Return an iterator over the keys of the dictionary."""
        return iter(self._data)

    def __len__(self) -> int:
        """Return the number of items in the dictionary."""
        return len(self._data)

    def __repr__(self) -> str:
        """Return a string representation of the DotDict."""
        return f"DotDict({self.as_dict()})"

    def __bool__(self) -> bool:
        """Return True if the DotDict is not empty."""
        return bool(self._data)

    def __copy__(self) -> DotDict:
        """Return a shallow copy of the DotDict."""
        return self.copy()

    def __deepcopy__(self, memo: dict[int, Any] | None = None) -> DotDict:
        """Return a deep copy of the DotDict."""
        if memo is None:
            memo = {}
        copied_data = copy.deepcopy(self._data, memo)
        return DotDict(copied_data)

    def copy(self) -> DotDict:
        """Return a shallow copy of the DotDict."""
        return DotDict(self.as_dict())

    def as_dict(self, json: bool = False, indent: bool = False, sort_keys: bool = False) -> dict[str, Any]:
        """Return a standard dictionary representation of the DotDict."""

        def convert(value: Any) -> Any:
            if isinstance(value, DotDict):
                return {k: convert(v) for k, v in value._data.items()}
            if isinstance(value, dict):
                return {k: convert(v) for k, v in value.items()}
            return value

        result: dict[str, Any] = {k: convert(v) for k, v in self._data.items()}
        if json:
            return _json.dumps(result, indent=4 if indent else None, sort_keys=sort_keys)
        return result

    def freeze(self) -> dict[str, Any]:
        """Return a frozen (immutable) version of the dictionary."""
        return freeze(self.as_dict())

    @classmethod
    def to_dot(cls, data: dict[str, Any]) -> Self:
        """Convert a standard dictionary to a DotDict."""
        dot: Self = cls()
        for key, value in data.items():
            if isinstance(value, dict):
                dot._data[key] = cls.to_dot(value)
            else:
                dot._data[key] = value
        return dot


__all__ = ["DotDict"]

if __name__ == "__main__":
    data = {
        "collection": {
            "item1": {"name": "Item 1", "value": 10},
            "item2": {"name": "Item 2", "value": {"subvalue": 20}},
        },
    }
    dot_data = DotDict.to_dot(data)
    print(dot_data)

    value = dot_data.collection.item1.name
    print(">>>> value = dot_data.collection.item1.name")
    print(value)  # Output: Item 1
    item_value = dot_data["collection"]["item1"]["name"]
    print(">>>> item_value = dot_data['collection']['item1']['name']")
    print(item_value)  # Output: Item 1
    print(f"Value is the same: {value == item_value}")

    print(">>>> dot_data.counter = 0")

    dot_data.counter = 0
    print(dot_data.counter)  # Output: 0
    print(">>>> dot_data.counter += 1")
    dot_data.counter += 1
    print(dot_data.counter)  # Output: 1
