"""Sentinel values for various purposes."""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from singleton_base import SingletonBase

if TYPE_CHECKING:
    from bear_dereth.typing_tools import LitFalse


@final
class Nullish(SingletonBase):
    """A sentinel value to indicate a null value, no default, or exit signal.

    Similar to a `None` type but distinct for configuration and control flow
    that might handle `None` as a valid value.
    """

    def value(self) -> None:
        """Return None to indicate no default value."""
        return None  # noqa: RET501

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Nullish)

    def __ne__(self, other: object) -> bool:
        return not isinstance(other, Nullish)

    def __bool__(self) -> LitFalse:
        return False

    def __hash__(self) -> int:
        return hash("__nullish__")

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return "<Nullish>"


NO_DEFAULT: Nullish = Nullish()
"""A sentinel value to indicate no default value."""

EXIT_SIGNAL: Nullish = Nullish()
"""A sentinel value to indicate an exit signal."""

CONTINUE: Nullish = Nullish()
"""A sentinel value to indicate continuation in an iteration or process."""
