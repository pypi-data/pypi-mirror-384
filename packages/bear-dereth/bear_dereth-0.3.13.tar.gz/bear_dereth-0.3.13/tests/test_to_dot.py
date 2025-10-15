from __future__ import annotations

from typing import Any

from bear_dereth.data_structs.to_dot import DotDict


def test_dotdict_attribute_access_and_assignment() -> None:
    data: dict[str, dict[str, dict[str, int]]] = {"alpha": {"beta": {"value": 1}}}
    dot = DotDict(data)

    assert dot.alpha.beta.value == 1
    dot.alpha.beta.value = 2
    assert dot["alpha"]["beta"]["value"] == 2

    dot.gamma = {"delta": 3}
    assert dot.gamma["delta"] == 3
    del dot.gamma
    assert "gamma" not in dot.as_dict()


def test_dotdict_copy_and_freeze_behaviour() -> None:
    dot = DotDict({"numbers": {"one": 1}})

    dot_copy: DotDict = dot.copy()
    dot_deepcopy: DotDict = dot.__deepcopy__(None)

    dot.numbers.two = 2
    assert dot_copy.numbers.one == 1
    assert "two" not in dot_copy.numbers.as_dict()
    assert "two" not in dot_deepcopy.numbers.as_dict()

    frozen = dot.freeze()
    assert frozen["numbers"]["two"] == 2
    assert isinstance(frozen, dict)


def test_dotdict_as_dict_to_dot_round_trip() -> None:
    initial: dict[str, dict[str, dict[str, int]]] = {"alpha": {"beta": {"value": 10}}}
    dot: DotDict = DotDict.to_dot(initial)

    assert isinstance(dot, DotDict)
    assert dot.alpha.beta.value == 10

    restored: dict[str, Any] = dot.as_dict()
    assert restored == initial
