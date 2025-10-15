"""A collection of operations that can be applied to fields in a document."""

from collections.abc import Callable
from contextlib import suppress
from operator import abs as _abs, mod as _mod, not_ as invert, pow as _pow
from typing import Any, Literal

from bear_dereth.operations.factories import FuncContainer, inject_ops


@inject_ops
def delete(field: str, ctx: FuncContainer) -> None:
    """Delete a given field from the document.

    Args:
        field: The field to delete.
    """
    ctx.deleter(field)


@inject_ops
def add(field: str, n: int, ctx: FuncContainer) -> None:
    """Add ``n`` to a given field in the document.

    Args:
        field: The field to add to.
        n: The amount to add.
    """
    attr: Any = ctx.getter(field)
    if isinstance(attr, (int | float)):
        ctx.setter(field, attr + n)


@inject_ops
def subtract(field: str, n: int, ctx: FuncContainer) -> None:
    """Subtract ``n`` to a given field in the document.

    Args:
        field: The field to subtract from.
        n: The amount to subtract.
    """
    attr = ctx.getter(field)
    if isinstance(attr, (int | float)):
        ctx.setter(field, attr - n)


@inject_ops
def multiply(field: str, n: int, ctx: FuncContainer) -> None:
    """Multiply a given field in the document by n.

    Args:
        field: The field to multiply.
        n: The amount to multiply by.
    """
    attr = ctx.getter(field)
    if isinstance(attr, (int | float)):
        ctx.setter(field, attr * n)


@inject_ops
def div(field: str, n: int, floor: bool, ctx: FuncContainer) -> None:
    """Divide a given field in the document by n.

    Args:
        field: The field to divide.
        n: The amount to divide by. Must not be zero
        floor: If True, use floor division.
    """
    attr = ctx.getter(field)
    if isinstance(attr, (int | float)) and n != 0:
        if floor:
            ctx.setter(field, attr // n)
        else:
            ctx.setter(field, attr / n)


@inject_ops
def increment(field: str, ctx: FuncContainer) -> None:
    """Increment a given field by 1."""
    attr = ctx.getter(field)
    if isinstance(attr, (int | float)):
        ctx.setter(field, attr + 1)


@inject_ops
def decrement(field: str, ctx: FuncContainer) -> None:
    """Decrement a given field in the document by 1.

    Args:
        field: The field to decrement.
    """
    attr = ctx.getter(field)
    if isinstance(attr, (int | float)):
        ctx.setter(field, attr - 1)


@inject_ops
def setter(field: str, v: Any, ctx: FuncContainer) -> None:
    """Set a given field to ``val``.

    Args:
        field: The field to set.
        v: The value to set the field to.
    """
    ctx.setter(field, v)


@inject_ops
def if_else(
    field: str,
    cond: Callable[[Any], bool],
    then: Callable[..., None],
    otherwise: Callable[..., None],
    ctx: FuncContainer,
) -> None:
    """Apply one of two operations based on the value of a field in the document.

    Args:
        field: The field to check.
        cond: A callable that takes the field's value and returns a boolean.
        then: The operation to apply if the condition is true.
        otherwise: The operation to apply if the condition is false.
    """

    def transform(doc: Any) -> None:
        if cond(ctx.getter(field)):
            then(doc)
        else:
            otherwise(doc)

    return transform(ctx.doc)


@inject_ops
def swapcase(field: str, ctx: FuncContainer) -> None:
    """Swap the case of a string field.

    Args:
        field: The field to swap case.
    """
    attr: Any = ctx.getter(field)
    if isinstance(attr, str):
        ctx.setter(field, attr.swapcase())


@inject_ops
def upper(field: str, ctx: FuncContainer) -> None:
    """Convert a string field to uppercase.

    Args:
        field: The field to convert.
    """
    attr = ctx.getter(field)
    if isinstance(attr, str):
        ctx.setter(field, attr.upper())


@inject_ops
def lower(field: str, ctx: FuncContainer) -> None:
    """Convert a string field to lowercase.

    Args:
        field: The field to convert.
    """
    attr = ctx.getter(field)
    if isinstance(attr, str):
        ctx.setter(field, attr.lower())


@inject_ops
def replace(field: str, old: str, new: str, ctx: FuncContainer) -> None:
    """Replace occurrences of a substring in a string field.

    Args:
        field: The field to modify.
        old: The substring to replace.
        new: The substring to replace with.
    """
    attr = ctx.getter(field)
    if isinstance(attr, str):
        ctx.setter(field, attr.replace(old, new))


@inject_ops
def format(field: str, ctx: FuncContainer, **kwargs: Any) -> None:
    """Format a string field using the provided arguments.

    Args:
        field: The field to format.
        **kwargs: Keyword arguments for formatting.
    """
    attr = ctx.getter(field)
    if isinstance(attr, str) and kwargs.get("kwargs") and isinstance(kwargs["kwargs"], dict):
        extracted = kwargs.pop("kwargs")
        attr: str = attr.format(**extracted)
        ctx.setter(field, attr)
    else:
        ctx.setter(field, attr.format(**kwargs))


@inject_ops
def pow(field: str, n: int, ctx: FuncContainer) -> None:
    """Raise a given field in the document to the power of n.

    Args:
        field: The field to raise.
        n: The exponent.
    """
    attr = ctx.getter(field)
    if isinstance(attr, (int | float)):
        ctx.setter(field, _pow(attr, n))


@inject_ops
def clamp(field: str, min_value: int, max_value: int, ctx: FuncContainer) -> None:
    """Clamp a given field in the document to be within min_value and max_value.

    Args:
        field: The field to clamp.
        min_value: The minimum value to clamp to.
        max_value: The maximum value to clamp to.
    """
    attr = ctx.getter(field)
    if isinstance(attr, (int | float)):
        ctx.setter(field, max(min_value, min(max_value, attr)))


@inject_ops
def mod(field: str, n: int, ctx: FuncContainer) -> None:
    """Modulus a given field in the document by n.

    Args:
        field: The field to modulus.
        n: The amount to modulus by.
    """
    attr = ctx.getter(field)
    if isinstance(attr, (int | float)) and n != 0:
        ctx.setter(field, _mod(attr, n))


@inject_ops
def toggle(field: str, ctx: FuncContainer) -> None:
    """Toggle a boolean field.

    Args:
        field: The field to toggle.
    """
    attr = ctx.getter(field)
    if isinstance(attr, bool):
        ctx.setter(field, invert(attr))


@inject_ops
def abs(field: str, ctx: FuncContainer) -> None:
    """Set a field to its absolute value.

    Args:
        field: The field to set.
    """
    attr = ctx.getter(field)
    if isinstance(attr, (int | float)):
        ctx.setter(field, _abs(attr))


@inject_ops
def default(field: str, v: Any, replace_none: bool, ctx: FuncContainer) -> None:
    """Set a field to a default value if it does not exist.

    Args:
        field: The field to set.
        v: The default value to set the field to.
        replace_none: If True, also replace None values.
    """
    try:
        current = ctx.getter(field)
        if replace_none and current is None:
            ctx.setter(field, v)
    except (KeyError, AttributeError):
        ctx.setter(field, v)


@inject_ops
def push(field: str, v: Any, index: int, ctx: FuncContainer) -> None:
    """Push a value to a list field in the document at a specific index.

    Args:
        field: The field to push to.
        v: The value to push.
        index: The index to insert the value at. Defaults to -1 (the end of the list).
    """
    try:
        attr = ctx.getter(field)
    except (KeyError, AttributeError):
        attr = ctx.setter(field, [], return_val=True)

    if isinstance(attr, list):
        if index == -1 or index >= len(attr):
            attr.append(v)
        else:
            attr.insert(index, v)


@inject_ops
def append(field: str, v: Any, ctx: FuncContainer) -> None:
    """Append a value to a list field in the document.

    Args:
        field: The field to append to.
        v: The value to append.
    """
    try:
        attr = ctx.getter(field)
    except (KeyError, AttributeError):
        attr: list[Any] = ctx.setter(field, [], return_val=True)

    if isinstance(attr, list):
        attr.append(v)


@inject_ops
def prepend(field: str, v: Any, ctx: FuncContainer) -> None:
    """Prepend a value to a list field in the document.

    Args:
        field: The field to prepend to.
        v: The value to prepend.
    """
    try:
        attr = ctx.getter(field)
    except (KeyError, AttributeError):
        attr: list[Any] = ctx.setter(field, [], return_val=True)
    if isinstance(attr, list):
        attr.insert(0, v)


@inject_ops
def extend(field: str, vals: list, ctx: FuncContainer) -> None:
    """Extend a list field in the document with another list.

    Args:
        field: The field to extend.
        vals: The list of values to extend with.
    """
    try:
        attr = ctx.getter(field)
    except (KeyError, AttributeError):
        ctx.setter(field, [])
        attr: list[Any] = []

    if isinstance(attr, list):
        attr.extend(vals)


@inject_ops
def pop(field: str, index: int, ctx: FuncContainer) -> None:
    """Pop a value from a list field in the document.

    Args:
        field: The field to pop from.
        index: The index to pop. Defaults to -1 (the last item).
    """
    with suppress(IndexError, KeyError, AttributeError):
        attr = ctx.getter(field)
        if isinstance(attr, list) and -len(attr) <= index < len(attr):
            attr.pop(index)


def if_in_list(item: Any, lst: list | tuple) -> bool:
    """Check if an item is in a collection (list, tuple, or set).

    Args:
        item: The item to check for.
        lst: The collection to check within.

    Returns:
        bool: True if the item is in the collection, False otherwise.
    """
    return item in lst


def if_is_instance(item: Any, types: type | tuple[type, ...]) -> bool:
    """Check if an item is an instance of a given type or types.

    Args:
        item: The item to check.
        types: The type or tuple of types to check against.

    Returns:
        bool: True if the item is an instance of the given type(s), False otherwise.
    """
    return isinstance(item, types)


def always_true(*_, **__) -> Literal[True]:
    """A function that always returns True."""
    return True


# if __name__ == "__main__":
#     from dataclasses import dataclass
#     from typing import Any

#     @dataclass
#     class Sample:
#         name: str
#         age: int

#     doc1: dict[str, Any] = {"name": "Alice", "age": 30}
#     doc2 = Sample(name="Bob", age=25)

#     print("Before:", doc1)
#     print("Before:", doc2)

#     increment("age")(doc1)
#     increment("age")(doc2)

#     upper("name")(doc1)
#     upper("name")(doc2)

#     print("After increment and upper:", doc1)
#     print("After increment and upper:", doc2)

#     decrement("age")(doc1)
#     decrement("age")(doc1)
#     decrement("age")(doc2)
#     decrement("age")(doc2)

#     print("After decrement:", doc1)
#     print("After decrement:", doc2)
