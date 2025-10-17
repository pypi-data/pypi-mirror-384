"""Sentinel values for various purposes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

from singleton_base import SingletonBase

if TYPE_CHECKING:
    from bear_dereth.typing_tools import LitFalse


class Nullish(SingletonBase):
    """A sentinel value to indicate a null value, no default, or exit signal.

    Similar to a `None` type but distinct for configuration and control flow
    that might handle `None` as a valid value.

    Can be subclassed for specific sentinel types like `NO_DEFAULT`,
    `EXIT_SIGNAL`, `CONTINUE`, and `NOTSET`.

    All instances and subclasses of `Nullish` will be treated as equal to each other.
    """

    _name: str = "Nullish"

    def value(self) -> None:
        """Return None to indicate no default value."""
        return None  # noqa: RET501

    def __getitem__(self, key: object) -> Nullish:
        return self

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Nullish)

    def __ne__(self, other: object) -> bool:
        return not isinstance(other, Nullish)

    def __bool__(self) -> LitFalse:
        return False

    def __repr__(self) -> str:
        return self.__str__()

    def __hash__(self) -> int:
        return hash("__nullish__")

    def __str__(self) -> str:
        return f"<{self._name}>"


@final
class NoDefaultType(Nullish):
    """A sentinel value to indicate no default value."""

    _name: str = "NoDefault"


NO_DEFAULT: Final = NoDefaultType()
"""A sentinel value to indicate no default value."""


@final
class ExitSignalType(Nullish):
    """A sentinel value to indicate an exit signal."""

    _name: str = "ExitSignal"


EXIT_SIGNAL: Final = ExitSignalType()
"""A sentinel value to indicate an exit signal."""


@final
class ContinueType(Nullish):
    """A sentinel value to indicate continuation in an iteration or process."""

    _name: str = "Continue"


CONTINUE: Final = ContinueType()
"""A sentinel value to indicate continuation in an iteration or process."""


@final
class NotSetType(Nullish):
    """A sentinel value to indicate a value is not set."""

    _name: str = "NotSet"


NOTSET: Final = NotSetType()
"""A sentinel value to indicate a value is not set."""
UNSET: Final = NOTSET
"""Alias for NOTSET sentinel value."""
