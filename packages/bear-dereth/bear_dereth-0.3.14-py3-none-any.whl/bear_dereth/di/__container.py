"""A simple dependency injection container with metaclass magic."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, NamedTuple, TypeGuard, cast

from pydantic import BaseModel, Field

from bear_dereth.data_structs.priority_queue import PriorityQueue
from bear_dereth.di.__wiring import Provide
from bear_dereth.di._resources import Resource, Singleton

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import TracebackType

_ATTR_PATTERN = "_{attr}_{cls_name}"
CONTAINER_ATTR = "{cls_name}_meta_"
BASE_CLASS_NAME = "DeclarativeContainer"


def has_service_name(instance: Any) -> TypeGuard[Resource | Singleton]:
    """Check if a service is a Resource or Singleton and has a service_name attribute."""
    return isinstance(instance, (Resource | Singleton)) and hasattr(instance, "service_name")


def is_resource(instance: Any) -> TypeGuard[Resource | Singleton]:
    """Check if a service is a Resource or Singleton."""
    return isinstance(instance, (Resource | Singleton))


def get_attr_name(cls: Any, attr: str) -> str:
    """Get the class-specific attribute name."""
    return _ATTR_PATTERN.format(attr=attr, cls_name=cls.cls_name)


class ContainerAttrs(BaseModel):
    """Attributes for the container."""

    cls_name: str
    name_map: dict[str, str] = Field(default_factory=dict)
    resources: dict[str, Resource | Singleton] = Field(default_factory=dict)
    services: dict[str, Any] = Field(default_factory=dict)
    teardown_callbacks: PriorityQueue[TearDownCallback] = Field(default_factory=PriorityQueue)
    service_types: dict[str, type] = Field(default_factory=dict)
    backups: dict[str, Any] = Field(default_factory=dict)

    model_config = {"arbitrary_types_allowed": True}

    def model_post_init(self, context: Any) -> None:
        self.name_map: dict[str, str] = {
            "resources": get_attr_name(self, "resources"),
            "services": get_attr_name(self, "services"),
            "teardown_callbacks": get_attr_name(self, "teardown_callbacks"),
            "service_types": get_attr_name(self, "service_types"),
            "backups": get_attr_name(self, "backups"),
        }
        return super().model_post_init(context)

    def set_resources(self, og: dict[str, Any], cp: dict[str, Any], backups: dict[str, Any]) -> None:
        for attr_name, attr_value in cp.items():
            if attr_name.startswith("_"):
                continue
            if isinstance(attr_value, classmethod):
                continue
            if has_service_name(attr_value) and attr_value.service_name is None:
                attr_value.service_name = attr_name.lower()
            self.resources[attr_name.lower()] = attr_value
            backups[attr_name] = og[attr_name]
            del og[attr_name]

    def set_type_services(self, ns: dict[str, Any]) -> None:
        annotations: dict[str, Any] = ns.get("__annotations__", {})
        for service_name, service_type in annotations.items():
            if not service_name.startswith("_"):
                self.service_types[service_name.lower()] = service_type


class TearDownCallback(NamedTuple):
    """Information about a registered teardown callback."""

    priority: float
    name: str
    callback: Callable[[], None]


class DeclarativeContainerMeta(type):
    """Metaclass that captures service declarations and makes the injection magic work."""

    @property
    def container_name(cls) -> str:
        """Return the name of the container class."""
        return CONTAINER_ATTR.format(cls_name=cls.__name__)

    @property
    def attrs(cls) -> ContainerAttrs:
        """Return the container attributes."""
        if not hasattr(cls, cls.container_name):
            raise AttributeError(f"Container '{cls.__name__}' has no container attributes")
        return getattr(cls, cls.container_name)

    @property
    def resources(cls) -> dict[str, Resource | Singleton]:
        """Return all resources defined in the container."""
        return cls.attrs.resources

    @property
    def services(cls) -> dict[str, Any]:
        """Return all services defined in the container."""
        return cls.attrs.services

    @property
    def service_types(cls) -> dict[str, Any]:
        """Return all service types defined in the container."""
        return cls.attrs.service_types

    @property
    def teardown_callbacks(cls) -> PriorityQueue[TearDownCallback]:
        """Return all registered teardown callbacks."""
        return cls.attrs.teardown_callbacks

    @property
    def backups(cls) -> dict[str, Any]:
        """Return all backups of original class attributes."""
        return cls.attrs.backups

    @staticmethod
    def _no_subclass_check(bases: tuple[type, ...]) -> None:
        """Prevent subclassing of concrete containers."""
        for base in bases:
            if (
                hasattr(base, "__name__")
                and base.__name__ != BASE_CLASS_NAME
                and isinstance(base, DeclarativeContainerMeta)
            ):
                raise TypeError(
                    f"Cannot inherit from concrete container '{base.__name__}'. "
                    f"Only direct inheritance from '{BASE_CLASS_NAME}' is allowed. "
                    f"Consider composition or dependency injection instead."
                )

    def __new__(mcs, name: str, bases: tuple[type, ...], namespace: dict[str, Any]) -> DeclarativeContainerMeta:
        """Create a new container class with provider magic."""
        if name == BASE_CLASS_NAME:
            return super().__new__(mcs, name, bases, namespace)
        mcs._no_subclass_check(bases)
        attrs = ContainerAttrs(cls_name=name)
        attrs.set_resources(namespace, namespace.copy(), attrs.backups)
        attrs.set_type_services(namespace)
        namespace[CONTAINER_ATTR.format(cls_name=name)] = attrs
        cls = super().__new__(mcs, name, bases, namespace)
        if hasattr(cls, "attrs") and cls.attrs.resources:
            cls.start()
        return cls

    def __getattr__(cls, name: str) -> Any:
        """Return a Provide instance for any service name or the actual provider object."""
        if not hasattr(cls, "attrs"):
            raise AttributeError(f"'{cls.__name__}' has no attribute '{name}'")

        if cls.attrs and name in cls.attrs.name_map:
            return getattr(cls.attrs, name)

        if name.lower() in cls.attrs.resources or (name in cls.attrs.service_types and not name.startswith("_")):
            return Provide(name.lower(), cls)
        raise AttributeError(f"'{cls.__name__}' has no attribute '{name}'")

    def __setattr__(cls, name: str, value: Any) -> None:
        """Set an attribute on the container class."""
        if name in cls.attrs.name_map:
            setattr(cls.attrs, name, value)
        super().__setattr__(name, value)

    @property
    def get_all_shutdowns(cls) -> dict[str, Any]:
        """Return all services that have a shutdown method.

        This allows us to always know that these services have a valid shutdown method.

        Returns:
            dict[str, Any]: A dictionary of service names to service instances that have a shutdown method
            that are considered valid shutdown services.
        """
        return {k: v for k, v in cls.services.items() if hasattr(v, "shutdown") and callable(v.shutdown)}


class DeclarativeContainer(metaclass=DeclarativeContainerMeta):
    """A simple service container for dependency injection."""

    def __name__(self) -> str:
        """Return the name of the container class."""
        return self.__class__.__name__

    @classmethod
    def register(cls, name: str, instance: Any) -> None:
        """Register a service instance with a name and optional metadata."""
        cls.services[name.lower()] = instance

    @classmethod
    def get(cls, name: str) -> Any | None:
        if name.lower() in cls.services:
            return cls.services[name.lower()]
        return None

    @classmethod
    def get_all(cls) -> dict[str, Any]:
        """Get all registered services."""
        return cls.services.copy()

    @classmethod
    def get_all_types(cls) -> dict[str, Any]:
        """Get all registered service types."""
        return cls.attrs.service_types.copy()

    @classmethod
    def has(cls, name: str) -> bool:
        """Check if a service is registered."""
        return name.lower() in cls.services or hasattr(cls, name)

    @classmethod
    def override(cls, name: str, instance: Any) -> None:
        """Add an instance to the container using its class name as the key."""
        cls.attrs.services[name.lower()] = instance

    @classmethod
    def clear(cls) -> None:
        """Clear all registered services and metadata."""
        cls.attrs.services.clear()
        cls.attrs.resources.clear()

    @classmethod
    def start(cls) -> None:
        """Start all registered resources."""
        resources: dict[str, Singleton | Resource] = {k: v for k, v in cls.resources.items() if is_resource(v)}

        for name, resource in resources.items():
            instance: Any | None = resource.get()
            if instance is not None:
                cls.services[name] = instance
                cls.register_teardown(name, cast("Callable", resource.shutdown))

    @classmethod
    def register_teardown(cls, name: str, callback: Callable[[], None], priority: float = float("inf")) -> None:
        """Register a callback to be executed during shutdown.

        Args:
            name (str): The name of the teardown callback.
            callback (Callable[[], None]): The callback function to be executed during shutdown.
            priority (float, optional): The priority of the callback. Lower values indicate higher priority.
                Defaults to float('inf') indicating lowest priority.

        Example:
            -------
            ```python
            class AppContainer(DeclarativeContainer):
                db: Database


            db = Database()
            AppContainer.register("db", db)
            AppContainer.register_teardown(lambda: db.close())
            AppContainer.shutdown()
        ```
        """
        if not callable(callback):
            return
        callback_info = TearDownCallback(priority=float(priority), name=name, callback=callback)
        cls.teardown_callbacks.put(callback_info)

    @classmethod
    def remove_teardown(cls, name: str) -> bool:
        """Remove a registered teardown callback by name.

        Args:
            name (str): The name of the teardown callback to remove.

        Returns:
            bool: True if the callback was found and removed, False otherwise.
        """
        return cls.teardown_callbacks.remove_element("name", name)

    @classmethod
    def shutdown(cls) -> None:
        """Shutdown services and execute registered teardown callbacks."""
        while cls.teardown_callbacks:
            callback_info: TearDownCallback = cls.teardown_callbacks.get()
            callback_info.callback()
        cls.clear()
        cls.teardown_callbacks.clear()

    @classmethod
    def __enter__(cls) -> type[DeclarativeContainer]:
        cls.start()
        return cls

    @classmethod
    def __exit__(
        cls, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None
    ) -> None:
        cls.shutdown()


# TODO: Maybe bring back for caching but for now, we aren't using it.
# @staticmethod
# def _get_metadata(instance: Any) -> FrozenDict:
#     """Get metadata about a service instance or class.

#     Args:
#         instance (Any): The service instance or class to get metadata for.

#     Returns:
#         FrozenDict: A frozen dictionary containing metadata about the service.
#     """
#     metadata: MetadataInfo = {
#         "type_name": "",
#         "module": "",
#         "is_class": False,
#         "id": 0,
#     }
#     is_class: TypeIs[type[Any]] = isclass(instance)
#     metadata["id"] = id(instance)
#     metadata["type_name"] = instance.__name__ if is_class else type(instance).__name__
#     metadata["module"] = (
#         getattr(instance, "__module__", "") if is_class else getattr(type(instance), "__module__", "")
#     )
#     metadata["is_class"] = is_class
#     return freeze(metadata)

# class MetadataInfo(TypedDict):
#     """Metadata information about a registered service."""

#     type_name: str
#     module: str
#     is_class: bool
#     id: int
