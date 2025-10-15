"""Async queue handler implementation for BearLogger with background processing."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from bear_dereth.di import Provide, inject
from bear_dereth.logger.common.log_level import LogLevel
from bear_dereth.logger.core.config import Container, LoggerConfig
from bear_dereth.logger.core.record import LoggerRecord
from bear_dereth.logger.handlers.queue_listener import QueueListener
from bear_dereth.logger.protocols.handler import Handler

if TYPE_CHECKING:
    from collections.abc import Callable
    from queue import Queue


class QueueHandler(Handler):
    """A handler that queues messages for async processing by target handlers."""

    default_mode_attr: ClassVar[str] = ""
    alt_mode_attr: ClassVar[str] = ""
    file: None = None  # QueueHandler does not use a file attribute # type: ignore[override]
    caller: QueueListener

    @inject
    def __init__(
        self,
        name: str = "queue",
        error_callback: Callable[..., Any] = Provide[Container.error_callback],
        root_level: Callable[[], LogLevel] = Provide[Container.root_level],
        config: LoggerConfig = Provide[Container.config],
        handlers: list[Handler] | None = None,
        level: LogLevel | str | int = LogLevel.DEBUG,
        max_queue_size: int = 1000,
    ) -> None:
        """Initialize the QueueHandler with comprehensive DI.

        Args:
            name: Handler name for identification
            error_callback: Callback for handling errors (from DI)
            root_level: Root logging level provider (from DI)
            config: Logger configuration (from DI)
            queue: Queue for async processing (from DI)
            handlers: List of handlers to forward messages to
            level: Minimum logging level for this handler
            max_queue_size: Maximum size of the message queue
        """
        super().__init__()
        self.name: str | None = name
        self.config: LoggerConfig = config
        self.error_callback: Callable[..., Any] = error_callback
        self.get_level: Callable[..., LogLevel] = root_level
        self.level: LogLevel = LogLevel.get(level, default=self.get_level())
        self.max_queue_size: int = max_queue_size
        self.caller = QueueListener(handlers=handlers, config=self.config, error_callback=error_callback)
        self.queue: Queue = self.caller.queue

    def emit(self, msg: object, style: str, level: LogLevel, **kwargs) -> None:
        """Enqueue a log message for async processing.

        Args:
            msg: The message object to enqueue
            style: The Rich style/theme name to apply
            level: The logging level of the message
            **kwargs: Additional keyword arguments for Rich formatting
        """
        if self.disabled or level < self.level:
            return

        record = LoggerRecord(msg=msg, style=style, level=level, **kwargs)
        try:
            self.queue.put_nowait(record)
        except Exception as e:
            self.error_callback("Error enqueuing log record", error=e, name=self.name or "queue_handler")
