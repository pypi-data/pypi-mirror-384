from collections.abc import Callable
from typing import TYPE_CHECKING, Annotated, Union

from rich.console import Console

from bear_dereth.introspection import get_function_signature, introspect_types

if TYPE_CHECKING:
    from inspect import Parameter, Signature


def mock_func(a: int, b: str, c: float | None) -> None:
    pass


def mock_func_with_console(a: Console, b: str) -> None:
    pass


def mock_func_with_string_console(a: "Console", b: str) -> None:
    pass


def mock_introspect_types_with_no_annotation() -> None:
    pass


def mock_introspect_types_with_union(a: Union[Console, int]) -> None:  # noqa: UP007
    pass


def mock_introspect_types_with_str_union(a: "Union[Console, int]") -> None:  # noqa: UP007
    pass


def mock_introspect_types_with_annotated(a: "Annotated[Console, 'A console']") -> None:
    pass


def test_introspect_types_with_typed_annotation() -> None:
    sig: Signature = get_function_signature(mock_func)
    param_a: Parameter = sig.parameters["a"]
    resolved_type = introspect_types(param_a, mock_func)
    assert resolved_type is int


def test_introspect_types_with_newer_union_annotation() -> None:
    sig: Signature = get_function_signature(mock_func)
    param_c: Parameter = sig.parameters["c"]
    resolved_type = introspect_types(param_c, mock_func)
    assert resolved_type is float  # Should resolve to the first type in the Union


def test_introspect_types_with_console_annotation() -> None:
    sig: Signature = get_function_signature(mock_func_with_console)
    param_a: Parameter = sig.parameters["a"]
    resolved_type = introspect_types(param_a, mock_func_with_console)
    assert resolved_type is Console


def test_introspect_types_with_string_console_annotation() -> None:
    sig: Signature = get_function_signature(mock_func_with_string_console)
    param_a: Parameter = sig.parameters["a"]
    resolved_type = introspect_types(param_a, mock_func_with_string_console)
    assert resolved_type is Console


def test_introspect_types_with_unresolvable_string_annotation() -> None:
    sig: Signature = get_function_signature(mock_func)
    param_b: Parameter = sig.parameters["b"]
    resolved_type = introspect_types(param_b, mock_func, default=str)
    assert resolved_type is str


def test_introspect_types_with_older_union_annotation() -> None:
    sig: Signature = get_function_signature(mock_introspect_types_with_union)
    param_a: Parameter = sig.parameters["a"]
    resolved_type = introspect_types(param_a, mock_introspect_types_with_union)
    assert resolved_type is Console  # Should resolve to the first type in the Union


def test_introspect_types_with_string_union_annotation() -> None:
    sig: Signature = get_function_signature(mock_introspect_types_with_str_union)
    param_a: Parameter = sig.parameters["a"]
    resolved_type = introspect_types(param_a, mock_introspect_types_with_str_union)
    assert resolved_type is Console  # Should resolve to the first type in the Union


def test_introspect_types_with_annotated_console() -> None:
    sig: Signature = get_function_signature(mock_introspect_types_with_annotated)
    param_a: Parameter = sig.parameters["a"]
    resolved_type = introspect_types(param_a, mock_introspect_types_with_annotated)
    assert resolved_type is Console


def test_introspect_types_with_list_generic() -> None:
    """Test what happens with list[Console] - does it return list or Console?"""

    def mock_list_console(a: list[Console]) -> None:
        pass

    sig: Signature = get_function_signature(mock_list_console)
    param_a: Parameter = sig.parameters["a"]
    resolved_type = introspect_types(param_a, mock_list_console)
    assert resolved_type is not list
    assert resolved_type is Console


def test_resolve_callables() -> None:
    """Test what happens with Callable[[int, str], float] - does it return Callable or float?"""

    def mock_callable(a: Callable[[int, str], bool]) -> None:
        pass

    sig: Signature = get_function_signature(mock_callable)
    param_a: Parameter = sig.parameters["a"]
    resolved_type = introspect_types(param_a, mock_callable)
    assert isinstance(resolved_type, Callable)
    assert not isinstance(resolved_type, type)


def test_deeply_nested_types() -> None:
    """Test what happens with deeply nested types like Annotated[Union[Console, int], 'desc']"""

    def mock_deep_nest1(a: Annotated[Union[list[Console], str], "meta"]) -> None:  # noqa: UP007
        pass

    def mock_deep_nest2(a: Annotated[Union[Console, str], "meta"]) -> None:  # noqa: UP007
        pass

    sig: Signature = get_function_signature(mock_deep_nest1)
    param_a: Parameter = sig.parameters["a"]
    resolved_type = introspect_types(param_a, mock_deep_nest1)
    assert resolved_type is Console

    sig2: Signature = get_function_signature(mock_deep_nest2)
    param_a2: Parameter = sig2.parameters["a"]
    resolved_type2 = introspect_types(param_a2, mock_deep_nest2)
    assert resolved_type2 is Console
