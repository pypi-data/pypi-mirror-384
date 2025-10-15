from __future__ import annotations

from typing import Any

import pytest

from bear_dereth.data_structs.freezing import (
    BaseHashValue,
    BaseNotCacheable,
    FrozenDict,
    FrozenModel,
    NotCacheable,
    freeze,
    thaw,
)
from bear_dereth.data_structs.lru_cache import LRUCache


def test_lru_cache_respects_capacity_and_recency() -> None:
    cache: LRUCache[str, int] = LRUCache(capacity=2)
    cache.set("a", 1)
    cache.set("b", 2)

    # Access 'a' so it becomes most recently used
    assert cache.get("a") == 1

    cache.set("c", 3)  # Should evict 'b'

    assert "a" in cache
    assert "c" in cache
    assert "b" not in cache
    assert cache.length == 2


def test_lru_cache_accepts_frozen_keys_from_freeze_helpers() -> None:
    cache: LRUCache[FrozenDict, str] = LRUCache(capacity=2)

    original: dict[str, Any] = {"alpha": [1, 2], "beta": {"nested": True}}
    key: FrozenDict = freeze(original)
    cache.set(key, "payload")

    # same structure, new object; freezing should normalize it to equivalent key
    equivalent_key: FrozenDict = freeze({"alpha": [1, 2], "beta": {"nested": True}})
    assert cache.get(equivalent_key) == "payload"

    cache.set(freeze({"alpha": [3]}), "other")
    assert cache.length == 2


def test_lru_cache_get_with_default_and_missing_key() -> None:
    cache: LRUCache[str, int] = LRUCache()

    assert cache.get("missing") is None
    assert cache.get("missing", default=5) == 5

    cache.set("present", 42)
    assert cache["present"] == 42

    with pytest.raises(KeyError):
        _ = cache["absent"]


def test_lru_cache_rejects_unhashable_keys() -> None:
    cache: LRUCache[object, int] = LRUCache()

    with pytest.raises(TypeError):
        cache.set(["not", "hashable"], 1)  # type: ignore[list-item]


def test_lru_cache_delete_and_clear() -> None:
    cache: LRUCache[str, int] = LRUCache()
    cache["x"] = 10
    cache["y"] = 20

    del cache["x"]
    assert "x" not in cache
    assert cache.length == 1

    cache.clear()
    assert cache.length == 0


def test_freeze_and_thaw_round_trip_nested_structures() -> None:
    data: dict[str, Any] = {"alpha": [1, {"beta": {1, 2}}], "gamma": {"delta": "value"}}

    frozen: FrozenDict = freeze(data)
    assert isinstance(frozen, FrozenDict)
    assert frozen["alpha"][1]["beta"] == frozenset({1, 2})

    thawed: dict = thaw(frozen)
    assert thawed == data
    assert thawed is not data  # ensure new objects were created


class SampleFrozen(FrozenModel):
    name: str
    value: int


def test_frozen_model_hash_and_equality_behavior() -> None:
    item_a = SampleFrozen(name="demo", value=1)
    item_b = SampleFrozen(name="demo", value=1)
    item_c = SampleFrozen(name="demo", value=2)

    assert item_a == item_b
    assert hash(item_a) == hash(item_b)
    assert item_a != item_c

    # Ensure frozen dump produces FrozenDict
    dump: FrozenDict = item_a.frozen_dump()
    assert isinstance(dump, FrozenDict)
    assert dump["value"] == 1


def test_frozen_model_not_cacheable_instances_reject_hashing() -> None:
    not_cacheable = SampleFrozen(name="demo", value=1, cacheable=False)
    assert not_cacheable.cacheable is False

    with pytest.raises(TypeError):
        hash(not_cacheable)


def test_not_cacheable_singletons_raise_on_hash() -> None:
    sentinel = NotCacheable()
    with pytest.raises(TypeError):
        hash(sentinel)

    base_not_cacheable_first = BaseNotCacheable()
    base_not_cacheable_second = BaseNotCacheable()
    assert base_not_cacheable_first is base_not_cacheable_second

    with pytest.raises(TypeError):
        hash(base_not_cacheable_first)


def test_base_hash_value_combine_preserves_frozen_structure() -> None:
    first = BaseHashValue(value=[1])
    second = BaseHashValue(value=[2])

    combined: BaseHashValue = first.combine(second)
    assert isinstance(combined, BaseHashValue)
    assert combined.value == [first, second]
