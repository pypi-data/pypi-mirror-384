"""A set of helper functions for dynamic module loading."""

from collections.abc import Callable
import importlib
from importlib.abc import Loader
from importlib.machinery import ModuleSpec
import importlib.util
import sys
from types import ModuleType

# TODO: Devolop this further, this is still an experimental module


class LazyLoader(Loader):
    """A loader that defers loading a module until it is accessed."""

    def __init__(self, fullname: str, path: str | None = None) -> None:
        """Initialize the LazyLoader with the module's full name and optional path."""
        self.fullname: str = fullname
        self.path: str | None = path

    def load(self) -> ModuleType:
        """Load the module and return it."""
        spec: ModuleSpec | None = importlib.util.find_spec(self.fullname)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot find module named {self.fullname}") from None
        module: ModuleType = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.modules[self.fullname] = module
        return module

    def create_module(self, spec: ModuleSpec) -> ModuleType | None:  # noqa: ARG002
        """Create a module. Returning None uses the default module creation."""
        return None  # Use default module creation semantics

    def exec_module(self, module: ModuleType) -> None:
        """Execute the module. This is where the actual loading happens."""
        if self.path is not None:
            with open(self.path) as file:
                code: str = file.read()
            exec(code, module.__dict__)  # noqa: S102
        else:
            raise ImportError(f"Cannot load module {self.fullname} without a path")


def load_module_by_name(module_name: str) -> ModuleType | None:
    """Dynamically load a module by its name, returning None if not found.

    Args:
        module_name (str): The name of the module to load.

    Returns:
        ModuleType | None: The loaded module, or None if not found.
    """
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return None


def load_module(module_name: str) -> ModuleType:
    """Dynamically load a module by its name, raising ImportError if not found.

    Args:
        module_name (str): The name of the module to load.

    Returns:
        ModuleType: The loaded module.

    Raises:
        ImportError: If the module cannot be found or loaded.
    """
    module: ModuleType | None = load_module_by_name(module_name)
    if module is None:
        raise ImportError(f"Cannot find module named {module_name}")
    return module


def lazy(fullname: str) -> ModuleType:
    """Lazily load a module by its full name.

    Args:
        fullname (str): The full name of the module to load.

    Returns:
        ModuleType: The loaded module.

    Raises:
        ImportError: If the module cannot be found or loaded.
    """
    try:
        return sys.modules[fullname]
    except KeyError:
        spec: ModuleSpec | None = importlib.util.find_spec(fullname)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot find module named {fullname}") from None
        module: ModuleType = importlib.util.module_from_spec(spec)
        loader = importlib.util.LazyLoader(spec.loader)
        loader.exec_module(module)
        return module


def _load(module_name: str, item_name: str) -> object:
    """Load a specific item from a module."""
    module: ModuleType = lazy(module_name)
    item: object = getattr(module, item_name)
    return item


def load_class[T](module: str, item: str, expected_type: type[T]) -> type[T]:
    """Load a specific class from a module, raising TypeError if not of expected type."""
    cls = _load(module, item)
    if isinstance(cls, type) and isinstance(cls, expected_type):
        return cls
    raise TypeError(f"Item {item} in module {module} is not a subclass of {expected_type.__name__}")


def load_item[T](module: str, item: str, expected_type: type[T]) -> T:
    """Load a specific item from a module, raising TypeError if not of expected type."""
    module_item: object = _load(module, item)
    if isinstance(module_item, expected_type):
        return module_item
    raise TypeError(f"Item {item} in module {module} is not of type {expected_type.__name__}")


def conditional_import(
    module_name: str,
    condition: Callable[[], bool],
) -> ModuleType | None:
    """Conditionally load a module and execute callbacks based on the condition.

    Args:
        module_name (str): The name of the module to load.
        condition (Callable[[], bool]): A callable that returns True or False.
        if_true (Callable[[ModuleType], None]): A callable to execute if the condition is True, receiving the loaded module.
        otherwise (Callable[[], None] | None): An optional callable to execute if the condition is False.

    Raises:
        ImportError: If the module cannot be found or loaded when the condition is True.
    """
    if condition():
        module: ModuleType = load_module(module_name)
        return module
    return None
