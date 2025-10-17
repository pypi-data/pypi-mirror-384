"""Experimental provider registry extracted from DI container ideas.

This module explores splitting a service container into two layers:

1. **ProviderRegistry** - name → provider mapping with optional caching.
2. **LifecycleManager** - optional coordination for start/shutdown hooks.

It is intentionally lightweight so other systems (like the ToolContext
plugins) can depend on the registry without inheriting metaclass magic.
"""

# pragma: no cover - experimental module

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable
from contextlib import suppress
from dataclasses import dataclass, field
from typing import Any, Protocol, cast, runtime_checkable

from bear_dereth.sentinels import UNSET

Factory = Callable[[], Any]
ShutdownHook = Callable[[], None]


"""TODO:
CONCERNS TO ADDRESS:

Concern: No validation of callable factories before registration
Security Risk: Could allow injection of malicious callables
Fix: Add explicit callable validation in register_factory


NOTE: This is an experimental module and API may change dramatically.
No tests for this exist and things are still being worked out.
"""


@runtime_checkable
class ProviderProtocol[Value](Protocol):
    """Duck-typed protocol for providers."""

    def __call__(self) -> Value:
        """Return a value when called."""
        ...


@dataclass(slots=True)
class ProviderRecord[Value]:
    """Internal metadata kept for each registered provider."""

    name: str
    factory: ProviderProtocol[Value]
    cache_result: bool = False
    value: Any = field(default=UNSET)

    def resolve(self) -> Value:
        """Return the provider value, respecting cache settings."""
        if self.cache_result:
            if self.value is UNSET:
                self.value = self.factory()
            return self.value
        return self.factory()

    def reset(self) -> None:
        """Drop cached value if present."""
        self.value = UNSET


class ProviderRegistry:
    """Registry that maps names to provider records and resolves them on demand."""

    def __init__(self) -> None:
        """Initialize an empty provider registry."""
        self._records: dict[str, ProviderRecord[Any]] = {}

    # -- registration -------------------------------------------------

    def register_factory[Value](
        self,
        name: str,
        factory: ProviderProtocol[Value],
        *,
        cache_result: bool = False,
    ) -> None:
        """Register a callable provider."""
        if not callable(factory):
            raise TypeError("factory must be callable")
        self._records[name.lower()] = ProviderRecord(name=name, factory=factory, cache_result=cache_result)

    def register_instance[Value](self, name: str, instance: Value) -> None:  # type: ignore[override]
        """Register a static instance (always cached)."""
        self._records[name.lower()] = ProviderRecord(
            name=name,
            factory=lambda: instance,
            cache_result=True,
            value=instance,
        )

    def register_alias(self, alias: str, target: str) -> None:
        """Make ``alias`` resolve to ``target``."""
        target = target.lower()
        if target not in self._records:
            raise KeyError(f"No provider registered under '{target}'")
        self._records[alias.lower()] = self._records[target]

    # -- resolution ---------------------------------------------------

    def resolve[Value](self, name: str, *, default: Value | Any = UNSET) -> Value:
        """Resolve a provider by name."""
        record: ProviderRecord[Any] | None = self._records.get(name.lower())
        if record is None:
            if default is not UNSET:
                return cast("Value", default)
            raise KeyError(f"No provider registered under '{name}'")
        return cast("Value", record.resolve())

    def get[Value](self, name: str, default: Value | None = None) -> Value | None:
        """Convenience wrapper that never raises."""
        with suppress(KeyError):
            return self.resolve(name)
        return default

    # -- management ---------------------------------------------------

    def unregister(self, name: str) -> bool:
        """Remove a provider if present."""
        return self._records.pop(name.lower(), None) is not None

    def clear(self) -> None:
        """Remove all providers."""
        self._records.clear()

    def reset_cache(self, name: str | None = None) -> None:
        """Reset cached values for one provider or all."""
        if name is None:
            for record in self._records.values():
                record.reset()
            return
        if record := self._records.get(name.lower()):
            record.reset()

    def __contains__(self, name: str) -> bool:  # pragma: no cover - trivial
        return name.lower() in self._records

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._records)


class LifecycleManager:
    """Optional coordinator that pairs the registry with startup/shutdown hooks."""

    def __init__(self, registry: ProviderRegistry | None = None) -> None:
        """Initialize with an optional existing registry or create a new one."""
        self.registry: ProviderRegistry = registry or ProviderRegistry()
        self._startup_hooks: dict[str, Factory] = {}
        self._shutdown_hooks: dict[str, list[ShutdownHook]] = defaultdict(list)
        self._started: bool = False

    # -- lifecycle ----------------------------------------------------

    def register_resource(
        self,
        name: str,
        factory: Factory,
        *,
        shutdown: ShutdownHook | Iterable[ShutdownHook] | None = None,
    ) -> None:
        """Register a resource with startup/shutdown support."""
        self._startup_hooks[name.lower()] = factory
        self.registry.register_factory(name, factory, cache_result=True)
        if shutdown:
            hooks: Iterable[ShutdownHook] | tuple
            if isinstance(shutdown, Iterable) and not isinstance(shutdown, (str, bytes)):
                hooks = shutdown
            else:
                hooks = (shutdown,)
            self._shutdown_hooks[name.lower()].extend(hooks)

    def start(self) -> None:
        """Eagerly resolve all startup resources once."""
        if self._started:
            return
        for name in list(self._startup_hooks):
            self.registry.resolve(name)
        self._started = True

    def shutdown(self) -> None:
        """Call registered shutdown hooks in LIFO order and clear cache."""
        for hooks in reversed(tuple(self._shutdown_hooks.values())):
            for hook in hooks:
                with suppress(Exception):
                    hook()
        self.registry.reset_cache()
        self._started = False

    # -- convenience --------------------------------------------------

    def resolve[Value](self, name: str) -> Value:  # type: ignore[override]
        """Pass-through to registry resolve."""
        return self.registry.resolve(name)


# -- Example usage -------------------------------------------------------------
# ruff: noqa: S101
if __name__ == "__main__":
    registry = ProviderRegistry()
    registry.register_instance("config", {"env": "dev"})
    registry.register_factory("random", factory=lambda: 42)

    assert registry.resolve("config")["env"] == "dev"
    assert registry.resolve("random") == 42  # noqa: PLR2004

    lifecycle = LifecycleManager(registry=ProviderRegistry())

    def open_resource() -> dict[str, Any]:
        return {"connected": True}

    def close_resource() -> None:
        print("closing resource")

    lifecycle.register_resource("db", open_resource, shutdown=close_resource)
    lifecycle.start()
    assert lifecycle.resolve("db")["connected"] is True
    lifecycle.shutdown()
