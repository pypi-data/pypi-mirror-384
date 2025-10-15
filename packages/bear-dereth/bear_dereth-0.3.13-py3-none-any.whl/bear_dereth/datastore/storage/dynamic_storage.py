"""Dynamic storage factory and related utilities."""

from typing import Literal, overload

from bear_dereth.datastore.storage.base_storage import Storage
from bear_dereth.datastore.storage.json import JsonStorage
from bear_dereth.datastore.storage.jsonl import JSONLStorage
from bear_dereth.datastore.storage.memory import InMemoryStorage
from bear_dereth.datastore.storage.toml import TomlStorage
from bear_dereth.datastore.storage.xml import XMLStorage
from bear_dereth.datastore.storage.yaml import YamlStorage

StorageChoices = Literal["jsonl", "toml", "yaml", "xml", "memory", "json", "default"]

storage_map: dict[str, type[Storage]] = {
    "jsonl": JSONLStorage,
    "toml": TomlStorage,
    "yaml": YamlStorage,
    "xml": XMLStorage,
    "memory": InMemoryStorage,
    "json": JsonStorage,
    "default": JSONLStorage,
}


@overload
def get_storage[T](storage: Literal["jsonl"]) -> type[JSONLStorage]: ...
@overload
def get_storage[T](storage: Literal["toml"]) -> type[TomlStorage]: ...
@overload
def get_storage[T](storage: Literal["yaml"]) -> type[YamlStorage]: ...
@overload
def get_storage[T](storage: Literal["xml"]) -> type[XMLStorage]: ...
@overload
def get_storage[T](storage: Literal["memory"]) -> type[InMemoryStorage]: ...
@overload
def get_storage[T](storage: Literal["json"]) -> type[JsonStorage]: ...
@overload
def get_storage[T](storage: Literal["default"]) -> type[JSONLStorage]: ...


def get_storage[T](storage: StorageChoices = "default") -> type[T]:  # type: ignore[type-arg]
    """Factory function to get a storage instance based on the storage type."""
    storage_type: type[T] = storage_map.get(storage, storage_map["default"])  # type: ignore[type-arg]
    return storage_type
