from __future__ import annotations

from bear_dereth.sentinels import EXIT_SIGNAL, NO_DEFAULT, Nullish


def test_nullish_singleton_is_falsy_and_repr() -> None:
    a = Nullish()
    b = Nullish()

    assert bool(a) is False
    assert a is b  # Singleton behaviour
    assert repr(a) == "<Nullish>"


def test_sentinel_constants_are_singletons() -> None:
    assert isinstance(NO_DEFAULT, Nullish)
    assert isinstance(EXIT_SIGNAL, Nullish)
    assert NO_DEFAULT is EXIT_SIGNAL


def test_nullish_value_returns_none() -> None:
    assert NO_DEFAULT.value() is None
