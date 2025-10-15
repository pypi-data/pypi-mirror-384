from __future__ import annotations

from bear_dereth.files.file_cache.basic_cache import BasicCache


def test_basic_cache_add_and_iterate() -> None:
    cache: BasicCache[str] = BasicCache()
    assert cache.empty()

    cache.add("alpha")
    cache.add(["beta", "gamma"])

    assert list(cache) == ["alpha", "beta", "gamma"]
    assert len(cache) == 3
    assert cache


def test_basic_cache_extend_and_clear() -> None:
    cache: BasicCache[str] = BasicCache(["start"])

    cache.extend(item for item in ["more", "items"])
    assert list(cache) == ["start", "more", "items"]

    cache.clear()
    assert cache.empty()

    cache.invalidate()
    assert cache.empty()


def test_basic_cache_handles_dicts_and_nested_lists() -> None:
    cache: BasicCache[dict[str, int] | str] = BasicCache()

    cache.add({"a": 1})
    cache.add([{"b": 2}, [{"c": 3}]])

    assert list(cache) == [{"a": 1}, {"b": 2}, {"c": 3}]


def test_basic_cache_iterator_consumes_in_order() -> None:
    cache: BasicCache[str] = BasicCache(["a", "b", "c"])
    iterator = iter(cache)
    assert next(iterator) == "a"
    assert next(iterator) == "b"
    assert list(iterator) == ["c"]


def test_basic_cache_instances_have_isolated_storage() -> None:
    cache_one = BasicCache(["x"])
    cache_two = BasicCache(["y"])

    cache_one.add("one")
    cache_two.add("two")

    assert list(cache_one) == ["x", "one"]
    assert list(cache_two) == ["y", "two"]
