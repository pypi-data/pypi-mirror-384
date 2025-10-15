"""A set of utility functions and protocols for type validation, coercion, and inspection."""

from typing import Any, get_args as _get_args

from bear_dereth.exceptions import ObjectTypeError
from bear_dereth.typing_tools.builtin_tools import type_name


class TypeHelper[T]:
    """A helper class for type-related utilities."""

    def __init__(self, cls: type[T]) -> None:
        """Initialize with a class to provide type-related utilities."""
        self.cls: type[T] = cls

    @property
    def orig_bases(self) -> tuple[type, ...]:
        """Get the original bases of the class.

        Returns:
            tuple[type, ...]: The original bases of the class.
        """
        if not hasattr(self.cls, "__orig_bases__"):
            raise AttributeError(f"Class {self.name} does not have __orig_bases__ attribute.")
        return getattr(self.cls, "__orig_bases__", ())

    @property
    def name(self) -> str:
        """Get the name of the class.

        Returns:
            str: The name of the class.
        """
        return type_name(self.cls)

    @property
    def args(self) -> tuple[Any, ...]:
        """Get the type arguments of a subclass that inherits from a generic class.

        Returns:
            tuple[Any, ...] | None: The type arguments if available, otherwise None.
        """
        return _get_args(self.orig_bases[0])

    @property
    def tp_count(self) -> int:
        """Get the number of type parameters of a subclass that inherits from a generic class.

        Returns:
            int: The number of type parameters.
        """
        return len(self.args)

    def get_type_param(self, index: int = 0) -> type:
        """Get the type parameter at the specified index.

        Args:
            index (int): The index of the type parameter to retrieve. Defaults to 0.

        Returns:
            type: The type parameter at the specified index, or NoneType if not available.
        """
        if self.args is None:
            raise AttributeError(f"Class {self.name} does not have type parameters.")
        if index < 0 or index >= len(self.args):
            raise IndexError(f"Index {index} is out of range for type parameters of class {self.name}.")
        return self.args[index]

    def validate_type(self, v: Any, exception: type[ObjectTypeError] | None = None) -> None:
        """Validate the type of the given value against the class type.

        Args:
            v (Any): The value to validate.
            exception (type[ObjectTypeError] | None): The exception to raise if the type
                does not match. If None, a TypeError is raised.
        """
        if not isinstance(v, self.cls):
            if exception is None:
                raise TypeError(f"Expected object of type {self.name}, but got {type_name(v)}.")
            raise exception(expected=self.cls, received=type(v))


def type_param(cls: type, index: int = 0) -> type:
    """Get the type parameter of a subclass that inherits from a generic class.

    Args:
        cls (type): The class to inspect.
        index (int): The index of the type parameter to retrieve. Defaults to 0.

    Returns:
        type: The type parameter at the specified index, or NoneType if not available.
    """
    return TypeHelper(cls).get_type_param(index=index)


def validate_type(v: Any, expected: type, exception: type[ObjectTypeError] | None = None) -> None:
    """Validate the type of the given value.

    Args:
        v (Any): The value to validate.
        expected (type): The expected type of the value.
        exception (type[ObjectTypeError] | None): The exception to raise if the type
            does not match. If None, a TypeError is raised.
    """
    TypeHelper(expected).validate_type(v=v, exception=exception)


def num_type_params(cls: type) -> int:
    """Get the number of type parameters of a subclass that inherits from a generic class.

    Args:
        cls (type): The class to inspect.

    Returns:
        int: The number of type parameters.
    """
    return TypeHelper(cls).tp_count


__all__ = ["TypeHelper", "num_type_params", "type_param", "validate_type"]

# if __name__ == "__main__":
#     from bear_epoch_time import EpochTimestamp

#     helper = TypeHelper(EpochTimestamp)
#     print(helper.name)  # Output: EpochTimestamp
