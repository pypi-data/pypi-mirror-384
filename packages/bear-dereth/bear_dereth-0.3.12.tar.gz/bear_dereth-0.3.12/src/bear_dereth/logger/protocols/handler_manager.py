"""A module defining a protocol for managing and routing messages to handlers."""

from typing import Any, Protocol, Self

from bear_dereth.logger.protocols.handler import Handler


class BaseHandlerManager(Protocol):
    """A minimal protocol for managing and routing messages to handlers."""

    handlers: list[Handler[Any]]

    def __init__(self) -> None:
        """Initialize the handler manager."""

    def add_handler(self, handler: Handler[Any]) -> None:
        """Add a handler to the logger."""
        if handler not in self.handlers:
            self.handlers.append(handler)

    def remove_handler(self, handler: Handler[Any]) -> None:
        """Remove a handler from the logger."""
        if handler in self.handlers:
            self.handlers.remove(handler)

    def clear_handlers(self) -> None:
        """Remove all handlers."""
        self.handlers.clear()

    def _emit_to_handlers(self, msg: object, style: str, *args, **kwargs) -> None:
        """Emit a message to all handlers with error handling."""

    def has_handlers(self) -> bool:
        """Check if any handlers are registered."""
        return len(self.handlers) > 0

    def close(self) -> None:
        """Close all handlers and clean up resources."""

    def flush(self) -> None:
        """Flush all handlers."""

    def __enter__(self) -> Self:
        """Enter the runtime context related to this object."""
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        """Exit the runtime context related to this object."""
