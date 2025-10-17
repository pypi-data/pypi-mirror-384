"""Functions that operate on functions, this is considered experimental."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bear_dereth.data_structs.const import Const
from bear_dereth.lazy_imports import lazy

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from types import ModuleType

    from bear_dereth.typing_tools import LitFalse, LitTrue

random: ModuleType = lazy("random")
inspect: ModuleType = lazy("inspect")


def const[T](value: T) -> Const[T]:
    """Create a constant function that always returns the given value.

    Use thius when you just need the value to be returned by a function, but
    don't care about the arguments. If you want to have more control over
    the arguments, use the `Const` class directly.

    Args:
        value (Any): The value to be returned by the constant function.

    Returns:
        Callable[..., Any]: A function that takes any arguments and returns the specified value.
    """
    return Const[T](value)


def identity[T](x: T) -> T:
    """Return the input value unchanged.

    Args:
        x (T): The input value.

    Returns:
        T: The same input value.
    """
    return x


def compose(*funcs: Callable) -> Callable:
    """Compose multiple functions into a single function.

    Args:
        *funcs (Callable): Functions to compose. The functions are applied
            from right to left.

    Returns:
        Callable: A new function that is the composition of the input functions.
    """
    if not funcs:
        return identity

    def composed(x: Any) -> Any:
        """Apply the composed functions to the input value."""
        for f in reversed(funcs):
            x = f(x)
        return x

    return composed


def pipe(value: Any, *funcs: Callable) -> Any:
    """Pipe a value through a series of functions.

    Args:
        value (Any): The initial value to be processed.
        *funcs (Callable): Functions to apply to the value in sequence.

    Returns:
        Any: The final result after applying all functions.
    """
    for func in funcs:
        value = func(value)
    return value


def complement(f: Callable[[Any], bool]) -> Callable[[Any], bool]:
    """Return the complement of a predicate function.

    Args:
        f (Callable[[Any], bool]): A predicate function that returns a boolean value.

    Returns:
        Callable[[Any], bool]: A new function that returns the opposite boolean value of the input function.
    """

    def complemented(*args: Any, **kwargs: Any) -> bool:
        return not f(*args, **kwargs)

    return complemented


def seed_rng(seed: int | None = None) -> None:
    """Seed the random number generator.

    Args:
        seed (int | None, optional): The seed value. If None, the RNG is seeded
            with the current system time or entropy source. Defaults to None.
    """
    random.seed(seed)


def rnd_int(low: int, high: int) -> int:
    """Generate a random integer between low and high, inclusive.

    Args:
        low (int): The lower bound of the range.
        high (int): The upper bound of the range.

    Returns:
        int: A random integer between low and high.
    """
    return random.randint(low, high)


def rnd_float(low: float, high: float) -> float:
    """Generate a random float between low and high.

    Args:
        low (float): The lower bound of the range.
        high (float): The upper bound of the range.

    Returns:
        float: A random float between low and high.
    """
    return random.uniform(low, high)


def rnd_bool(chance: float = 0.5) -> bool:
    """Generate a random boolean value based on a given chance.

    Args:
        chance (float, optional): The probability of returning True. Defaults to 0.5.

    Returns:
        bool: A random boolean value, True with the specified probability.
    """
    return random.random() < chance


def choice[T](seq: Sequence[T]) -> T:
    """Select a random element from a non-empty sequence.

    Args:
        seq (Sequence[T]): A non-empty sequence (like a list or tuple) to choose from.

    Returns:
        T: A randomly selected element from the sequence.

    Raises:
        IndexError: If the sequence is empty.
    """
    if not seq:
        raise IndexError("Cannot choose from an empty sequence")
    return random.choice(seq)


def has_attrs(seq: object, attrs: Sequence[str], true_only: bool = False) -> dict[str, bool]:
    """Check if an object has all specified attributes.

    Args:
        obj (Any): The object to check.
        attrs (list[str]): A list of attribute names to check for.

    Returns:
        dict[str, bool]: A dictionary mapping each attribute name to a boolean indicating its presence.
    """
    out: dict[str, bool] = {attr: hasattr(seq, attr) for attr in attrs}
    if true_only:
        out = {k: v for k, v in out.items() if v}
    return out


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


def always_true(*_, **__) -> LitTrue:
    """A function that always returns True."""
    return True


def always_false(*_, **__) -> LitFalse:
    """A function that always returns False."""
    return False


def get_instance(service: type | Any) -> Any | None:
    """Get the service instance, instantiating if necessary.

    Args:
        service (Any): The service class or instance.
    """
    try:
        if inspect.isclass(service):
            return service()
        return service
    except Exception:
        return None
