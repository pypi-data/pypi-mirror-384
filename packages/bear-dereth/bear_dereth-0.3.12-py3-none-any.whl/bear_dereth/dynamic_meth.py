"""Module providing a class decorator to add methods dynamically with proper parameter binding."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from bear_dereth.introspection import get_function_signature
from bear_dereth.logger.protocols import TypeLogger

if TYPE_CHECKING:
    from inspect import BoundArguments, Signature


def dynamic_methods[T](
    methods: dict[str, dict[str, Any]] | BaseModel,
    delegate_to: str,
    doc: str | None = None,
) -> Callable[..., T]:  # type: ignore[misc] # This is fine but pyright is confused
    """Class decorator that adds methods dynamically with proper parameter binding.

    Args:
        methods: A dictionary where keys are method names and values are dictionaries of keyword arguments
                    to be passed to the delegated method. It can also be a Pydantic BaseModel instance with
                    fields representing method names and their corresponding keyword arguments. It will
                    be converted to a dictionary using `model_dump(exclude_none=True)`.
        delegate_to: The name of the method to which the new methods will delegate.
        doc: Optional docstring template for the new methods. If provided, it should include placeholders
             `{name}` for the method name and `{delegate_to}` for the delegated method name.

    Returns:
        A class decorator that adds the specified methods to the decorated class.
    """
    if isinstance(methods, BaseModel):
        methods = methods.model_dump(exclude_none=True)

    def decorator(cls: T) -> T:
        def create_method(name: str, method_kwargs: dict[str, Any]) -> Callable:
            def method[Return_T: Callable](self: T, *args, **kwargs) -> Return_T:  # type: ignore[misc] # This is fine but pyright is confused
                base_method: Any = getattr(self, delegate_to)
                sig: Signature = get_function_signature(base_method)
                bound: BoundArguments = sig.bind_partial(*args)
                final_kwargs: dict[str, Any] = {**method_kwargs, **kwargs}
                return base_method(*bound.args, **final_kwargs)

            default_doc = "Dynamically added method '{name}' that delegates to '{delegate_to}'."

            method.__name__ = name
            method.__doc__ = (
                doc.format(name=name, delegate_to=delegate_to)
                if doc
                else default_doc.format(name=name, delegate_to=delegate_to)
            )
            return method

        for method_name, method_kwargs in methods.items():
            if not hasattr(cls, method_name):
                setattr(cls, method_name, create_method(method_name, method_kwargs))

        return cls

    return decorator


if __name__ == "__main__":
    METHODS: dict[str, dict[str, str]] = {
        "info": {"style": "info", "level": "INFO"},
        "warning": {"style": "warning", "level": "WARNING"},
        "error": {"style": "error", "level": "ERROR"},
        "exception": {"style": "exception", "level": "EXCEPTION"},
    }

    @dynamic_methods(methods=METHODS, delegate_to="_wrapped_print")
    class MyLogger(TypeLogger):
        """A simple logger class to demonstrate dynamic method addition."""

        def _wrapped_print(self, msg: object, style: str, level: str, **kwargs) -> None:
            print(f"[{level}] ({style}): {msg}", **kwargs)

        def __getattr__(self, name: str) -> Any:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    logger = MyLogger()
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.exception("This is an exception message.")
