from collections.abc import Callable
from contextlib import suppress
from typing import Any

from bear_dereth.lazy_imports import lazy
from bear_dereth.operations import always_true

ast = lazy("ast")


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
    return "NONE"


if __name__ == "__main__":
    from bear_epoch_time import EpochTimestamp

    print(eval_to_native(EpochTimestamp))
