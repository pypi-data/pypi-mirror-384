"""Based upon the standard library logging.handlers.QueueListener."""

from collections.abc import Callable
import queue
from queue import Queue
import threading
from typing import Any, Self

from bear_dereth.di import Provide, inject
from bear_dereth.logger.core.config import Container, LoggerConfig
from bear_dereth.logger.core.record import LoggerRecord
from bear_dereth.logger.protocols import BaseHandlerManager, Handler
from bear_dereth.sentinels import EXIT_SIGNAL


class QueueListener(BaseHandlerManager):  # We can add support for asyncio.Queue later if needed?
    """This class implements an internal threaded listener."""

    @inject
    def __init__(
        self,
        config: LoggerConfig = Provide[Container.config],
        error_callback: Callable[..., Any] = Provide[Container.error_callback],
        handlers: list[Handler] | None = None,
        respect_handler_level: bool = False,
    ) -> None:
        """Initialise an instance with the specified queue and handlers."""
        self.config: LoggerConfig = config
        self.error_callback: Callable[..., Any] = error_callback
        self.queue: Queue = config.queue.queue
        self.handlers: list[Handler[Any]] = handlers if handlers is not None else []
        self._thread = None
        self.respect_handler_level: bool = respect_handler_level

    def __enter__(self) -> Self:
        """For use as a context manager. Starts the listener."""
        self.start()
        return self

    def __exit__(self, *args) -> None:
        """For use as a context manager. Stops the listener."""
        self.stop()

    def dequeue(self, block: bool) -> LoggerRecord:
        """Dequeue a record and return it, optionally blocking.

        The base implementation uses get. You may want to override this method
        if you want to use timeouts or work with custom queue implementations.
        """
        return self.queue.get(block=block)

    def start(self) -> None:
        """Start the listener.

        This starts up a background thread to monitor the queue for
        LogRecords to process.
        """
        if self._thread is not None:
            raise RuntimeError("Listener already started")

        self._thread = t = threading.Thread(target=self._monitor)
        t.daemon = True
        t.start()

    def prepare(self, record: LoggerRecord) -> dict[str, Any]:
        """Prepare a record for handling."""
        return record.model_dump(exclude_none=True, exclude={"message_str", "has_stack_info", "has_timestamp"})

    def handle(self, record: LoggerRecord) -> None:
        """Handle a record.

        This just loops through the handlers offering them the record
        to handle.
        """
        try:
            record_dict: dict[str, Any] = self.prepare(record)
            for handler in self.handlers:
                if not self.respect_handler_level and record.level >= handler.level:
                    handler.emit(**record_dict)
        except Exception as e:
            self.error_callback("Error during QueueListener handle", error=e)

    def _monitor(self) -> None:
        """Monitor the queue for records, and ask the handler to deal with them.

        This method runs on a separate, internal thread.
        The thread will terminate if it sees a sentinel object in the queue.
        """
        q: Queue = self.queue
        has_task_done: bool = hasattr(q, "task_done")
        while True:
            try:
                record: LoggerRecord = self.dequeue(block=True)
                if record is EXIT_SIGNAL:
                    if has_task_done:
                        q.task_done()
                    break
                self.handle(record)
                if has_task_done:
                    q.task_done()
            except queue.Empty:
                break

    def enqueue_sentinel(self) -> None:
        """This is used to enqueue a sentinel object to tell the listener to stop.

        The base implementation uses put_nowait. You may want to override this
        method if you want to use timeouts or work with custom queue
        implementations.
        """
        self.queue.put_nowait(EXIT_SIGNAL)

    def stop(self) -> None:
        """Stop the listener.

        This asks the thread to terminate, and then waits for it to do so.
        Note that if you don't call this before your application exits, there
        may be some records still left on the queue, which won't be processed.
        """
        if self._thread:  # see gh-114706 - allow calling this more than once
            self.enqueue_sentinel()
            self._thread.join()
            self._thread = None
