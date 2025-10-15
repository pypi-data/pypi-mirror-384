"""General introspection utilities."""

from collections.abc import Callable
from functools import lru_cache
import inspect
from inspect import Signature
from typing import Any, get_type_hints


@lru_cache(maxsize=256)
def get_function_signature(func: Callable) -> Signature:
    """Get the signature of a function, cached for performance."""
    return inspect.signature(func)


@lru_cache(maxsize=256)
def find_type_hints(name: str, func: Callable) -> Any | None:
    """Get the type hint for a given parameter name in a function, cached for performance."""
    type_hints: dict[str, Any] = get_type_hints(func, globalns=func.__globals__)
    return type_hints.get(name)
