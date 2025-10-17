"""Factory for creating field operations that work for both mappings and objects."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from threading import RLock
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar, overload

from bear_dereth.di import Singleton
from bear_dereth.introspection import get_function_signature
from bear_dereth.lazy_imports import lazy
from bear_dereth.operations.common import PARAM_NAMES, PARAM_OPS, CollectionChoice, default_factory

typing_tools = lazy("bear_dereth.typing_tools")


if TYPE_CHECKING:
    from collections.abc import Callable
    from inspect import BoundArguments, Signature

Return = TypeVar("Return")
P = ParamSpec("P")
_lock = RLock()


# TODO: Combine these two factories into one with the ability to do more complex operations
# FUNCTIONAL PROGRAMMING PARADISE HERE WE COME


def uses_func_container(sig: Signature, bound: BoundArguments, container: FuncContext) -> BoundArguments:
    """Check if a function signature uses FuncContext in its parameters and return bound arguments."""
    for param in sig.parameters:
        if sig.parameters[param].annotation is FuncContext and param not in bound.arguments:
            bound.arguments[param] = container
    return bound


def is_func_container(sig: Signature, bound: BoundArguments) -> bool:
    """Check if a function signature uses FuncContext in its parameters and return bound arguments."""
    for param in sig.parameters:
        if sig.parameters[param].annotation is FuncContext and param not in bound.arguments:
            return True
    return False


class FuncContext[T]:
    """Context for a function that allows for functional operations on mappings and objects."""

    _singleton: Singleton[FuncContext] | None = None

    def __init__(self, doc: T | None = None) -> None:
        """Container for getter and setter functions for a specific field.

        Args:
            doc: The document (mapping or object) to operate upon.
        """
        self.doc: T = doc  # type: ignore[assignment]
        self.reval: Any = None

    def _return_value(self) -> Any:
        reval: Any = self.reval
        self.reval = None
        return reval

    def update(self, doc: T) -> None:
        """Update the document being operated on."""
        self.doc = doc

    def getter[V](self, f: str) -> V:  # type: ignore[override]
        """Get the value of the specified field from a mapping or object."""
        if typing_tools.is_mapping(self.doc):
            return self.doc[f]  # type: ignore[index]
        return getattr(self.doc, f)

    if TYPE_CHECKING:
        from bear_dereth.typing_tools import LitFalse, LitTrue

        @overload
        def setter[V](self, f: str, v: V, return_val: LitTrue) -> V: ...

        @overload
        def setter[V](self, f: str, v: V, return_val: LitFalse = False) -> None: ...  # type: ignore[override]

    def setter[V](self, f: str, v: V, return_val: bool = False) -> V | None:
        """Set the value of the specified field in a mapping or object."""
        if typing_tools.is_mapping(self.doc):
            self.doc[f] = v  # type: ignore[index]
            if return_val:
                self.reval = self.doc[f]  # type: ignore[index]
        else:
            setattr(self.doc, f, v)
            if return_val:
                self.reval = getattr(self.doc, f)
        return self._return_value()

    def deleter(self, f: str) -> None:
        """Delete the specified field from a mapping or object."""
        if typing_tools.is_mapping(self.doc):
            del self.doc[f]  # type: ignore[index]
        else:
            delattr(self.doc, f)

    def get(
        self,
        default: CollectionChoice | str = "dict",
        **kwargs,
    ) -> type[dict | list | set] | defaultdict | Callable[..., dict | list | set | defaultdict]:
        """Get the document being operated on."""
        if factory := kwargs.pop("factory", False):
            return factory
        match default:
            case "dict":
                return dict
            case "list":
                return list
            case "set":
                return set
            case "defaultdict":
                return defaultdict
            case _:
                return dict

    @classmethod
    def get_singleton(cls) -> FuncContext[T]:
        """Get the singleton instance of FuncContext."""
        with _lock:
            if cls._singleton is None:
                cls._singleton = Singleton(cls)
            return cls._singleton.get()


def inject_ops(op_func: Callable) -> Callable[..., Callable[..., None]]:
    """Create a field operation that works for both mappings and objects."""

    def op_factory[T](*args, **kwargs) -> Callable[..., None]:
        def transform(*subargs) -> None:
            container: FuncContext[T] = FuncContext.get_singleton()
            container.update(*subargs)
            s: Signature = get_function_signature(op_func)
            b: BoundArguments = s.bind_partial(*args, **kwargs)
            for param in PARAM_OPS:
                if param in s.parameters and param not in b.arguments:
                    b.arguments[param] = container
            for param in PARAM_NAMES:
                if param in s.parameters and param not in b.arguments:
                    b.arguments[param] = container
            if is_func_container(s, b):
                b = uses_func_container(s, b, container)
            b.apply_defaults()

            op_func(**b.arguments)

        return transform

    return op_factory


class Factory:
    """Decorator to inject a factory callable into a function's keyword arguments."""

    def inject(self, op_func: Callable) -> Callable[..., Callable[..., None]]:
        """Create a field operation that works for both mappings and objects."""

        def op_factory[T](*args, **kwargs) -> Callable[..., None]:
            def transform(*sub_args) -> None:
                doc: T = sub_args[0]
                container: FuncContext[T] = FuncContext.get_singleton()
                container.update(doc)
                s: Signature = get_function_signature(op_func)
                b: BoundArguments = s.bind_partial(*args, **kwargs)
                for param in PARAM_OPS:
                    if param in s.parameters and param not in b.arguments:
                        b.arguments[param] = container
                for param in PARAM_NAMES:
                    if param in s.parameters and param not in b.arguments:
                        b.arguments[param] = container
                if is_func_container(s, b):
                    b = uses_func_container(s, b, container)
                b.apply_defaults()

                op_func(**b.arguments)

            return transform

        return op_factory


# TODO: Fold into inject_ops above somehow
class Inject:
    """Decorator to inject a factory callable into a function's keyword arguments."""

    def __init__(self, choice: CollectionChoice = "dict") -> None:
        """Decorator to inject a factory callable into a function's keyword arguments."""
        self.choice = choice

    def factory(self, func: Callable[P, Return], default: Callable = default_factory) -> Callable[..., Return]:
        """Decorator to inject a factory callable into a function's keyword arguments.

        The factory callable is used to create new instances of a specified type,
        defaulting to the built-in `dict` if not provided.

        Args:
            func (Callable): The function to decorate.
            default_factory (Callable): Function to extract/create the factory. Defaults to _factory.

        Returns:
            Callable: The decorated function with factory injection.
        """
        from bear_dereth.introspection import get_function_signature

        def wrapper(*args, **kwargs) -> Return:
            sig: Signature = get_function_signature(func)
            bound: BoundArguments = sig.bind_partial(*args, **kwargs)
            if "factory" not in bound.arguments:
                bound.arguments["factory"] = default(choice=self.choice, **kwargs)
            bound.apply_defaults()
            return func(*bound.args, **bound.kwargs)

        return wrapper


# ruff: noqa: PLC0415
