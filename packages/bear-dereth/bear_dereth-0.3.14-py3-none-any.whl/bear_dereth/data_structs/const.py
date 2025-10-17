"""A module providing a constant function implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, final

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


class CannotModifyConstError(Exception):
    """Raised when attempting to modify a Const instance."""


class ConstantMeta(type):
    """A metaclass for creating immutable constant classes."""

    def __new__(mcs, name: str, bases: tuple[type, ...], namespace: dict[str, Any]) -> ConstantMeta:
        """Create a new Constant class."""
        cls = super().__new__(mcs, name, bases, namespace)
        original_setattr: Callable[[str, Any], None] = cls.__setattr__

        def locked_setattr(self: Any, key: str, value: Any) -> None:
            """I don't think so! 😤"""
            try:
                is_init = object.__getattribute__(self, "_init")
            except AttributeError:
                original_setattr(self, key, value)  # type: ignore[call-arg]
                return
            if is_init:
                if key in {"_Const__value", "value", "__value"}:
                    raise CannotModifyConstError("Cannot modify the value of a Const instance")
                raise CannotModifyConstError(f"Cannot modify attribute '{key}' of immutable Const")

            original_setattr(self, key, value)  # type: ignore[call-arg]

        cls.__setattr__ = locked_setattr  # type: ignore[assignment]
        return cls


@final
class Const[T](metaclass=ConstantMeta):
    """A callable that always returns the same constant value."""

    __slots__: tuple = ("__value", "_init")

    def __init__(self, value: T) -> None:
        """Initialize the Constant function with a fixed value."""
        self.__value: T = value
        self._init = True

    @property
    def value(self) -> T:
        """The sacred value!"""
        return self.__value

    @value.setter
    def value(self, _: Any) -> None:
        """Nawwwww! 😤"""
        raise CannotModifyConstError("Cannot modify the value of a Const instance")

    def __call__(self, *_: Any, **__: Any) -> T:
        """Return the constant value, ignoring any arguments."""
        return self.value

    def __eq__(self, other: object) -> bool:
        try:
            return self.value == getattr(other, "value") if hasattr(other, "value") else other  # type: ignore[operator] # noqa: B009
        except Exception:
            return False

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __lt__(self, other: object) -> bool:
        try:
            return self.value < getattr(other, "value") if hasattr(other, "value") else other  # type: ignore[operator] # noqa: B009
        except Exception:
            return False

    def __le__(self, other: object) -> bool:
        try:
            return self.value <= getattr(other, "value") if hasattr(other, "value") else other  # type: ignore[operator] # noqa: B009
        except Exception:
            return False

    def __gt__(self, other: object) -> bool:
        try:
            return self.value > getattr(other, "value") if hasattr(other, "value") else other  # type: ignore[operator] # noqa: B009
        except Exception:
            return False

    def __ge__(self, other: object) -> bool:
        try:
            return self.value >= getattr(other, "value") if hasattr(other, "value") else other  # type: ignore[operator] # noqa: B009
        except Exception:
            return False

    def __bool__(self) -> bool:
        return bool(self.value)

    def __iter__(self) -> Iterator[T]:
        if hasattr(self.value, "__iter__"):
            return iter(self.value)  # type: ignore[return-value]
        raise TypeError(f"{self.value} of type {type(self.value)} is not iterable")

    def __int__(self) -> int:
        if isinstance(self.value, int):
            return self.value
        raise TypeError(f"Cannot convert {self.value} of type {type(self.value)} to int")

    def __float__(self) -> float:
        if isinstance(self.value, (int | float)):
            return float(self.value)
        raise TypeError(f"Cannot convert {self.value} of type {type(self.value)} to float")

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:
        return f"Const({self.value})"
