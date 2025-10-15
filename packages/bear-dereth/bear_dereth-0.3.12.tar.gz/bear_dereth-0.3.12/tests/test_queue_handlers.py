from __future__ import annotations

from queue import Queue
import threading
from types import SimpleNamespace

from bear_dereth.logger.common.log_level import LogLevel
from bear_dereth.logger.core.record import LoggerRecord
from bear_dereth.logger.handlers.queue_handler import QueueHandler
from bear_dereth.logger.handlers.queue_listener import QueueListener
from bear_dereth.sentinels import EXIT_SIGNAL


def make_config(queue: Queue) -> SimpleNamespace:
    return SimpleNamespace(queue=SimpleNamespace(queue=queue))


class DummyHandler:
    def __init__(self) -> None:
        """A minimal handler that records emitted log records."""
        self.name = "dummy"
        self.level = LogLevel.DEBUG
        self.disabled = False
        self.mode = "default"
        self.caller = None
        self.file = None
        self.emitted: list[dict[str, object]] = []

    def emit(self, **record_dict) -> None:
        """Capture emitted log records."""
        self.emitted.append(record_dict)


def test_queue_listener_processes_records_until_sentinel() -> None:
    queue = Queue()
    handler = DummyHandler()
    errors: list[str] = []

    listener = QueueListener(
        config=make_config(queue),
        error_callback=lambda message, **kwargs: errors.append(message),
        handlers=[handler],
        respect_handler_level=False,
    )

    queue.put(LoggerRecord.create("first", level=LogLevel.INFO))
    queue.put(LoggerRecord.create("second", level=LogLevel.INFO))
    queue.put(EXIT_SIGNAL)

    listener._monitor()

    assert [rec["msg"] for rec in handler.emitted] == ["first", "second"]
    assert errors == []
    assert queue.empty()


def test_queue_listener_start_and_stop_controls_thread() -> None:
    queue = Queue()
    listener = QueueListener(
        config=make_config(queue),
        error_callback=lambda *args, **kwargs: None,
    )

    listener.start()
    assert listener._thread is not None
    assert listener._thread.is_alive()

    listener.stop()
    assert listener._thread is None


def test_queue_handler_emit_enqueues_logger_records() -> None:
    queue = Queue()
    errors: list[str] = []

    handler = QueueHandler(
        name="queue",
        error_callback=lambda message, **kwargs: errors.append(message),
        root_level=lambda: LogLevel.INFO,
        config=make_config(queue),
        handlers=[],
        level=LogLevel.DEBUG,
    )

    handler.emit(msg="hello", style="", level=LogLevel.INFO)

    record = queue.get_nowait()
    assert isinstance(record, LoggerRecord)
    assert record.msg == "hello"
    assert errors == []


def test_queue_handler_respects_level_and_queue_full_errors() -> None:
    queue = Queue(maxsize=1)
    captured: list[tuple[str, dict[str, object]]] = []

    handler = QueueHandler(
        name="queue",
        error_callback=lambda message, **kwargs: captured.append((message, kwargs)),
        root_level=lambda: LogLevel.INFO,
        config=make_config(queue),
        handlers=[],
        level=LogLevel.INFO,
    )

    # Level lower than handler threshold -> should not enqueue
    handler.emit(msg="ignored", style="", level=LogLevel.DEBUG)
    assert queue.empty()

    # Fill queue and trigger put failure
    queue.put(LoggerRecord.create("existing"))
    handler.emit(msg="will-fail", style="", level=LogLevel.INFO)

    assert captured, "Expected an error to be captured"
    assert captured[0][0] == "Error enqueuing log record", "Unexpected error message"


def test_queue_listener_processes_records_from_multiple_threads() -> None:
    queue = Queue()
    handler = DummyHandler()
    errors: list[str] = []

    listener = QueueListener(
        config=make_config(queue),
        error_callback=lambda message, **kwargs: errors.append(message),
        handlers=[handler],
    )

    listener.start()

    messages = [[f"t1-{i}" for i in range(3)], [f"t2-{i}" for i in range(3)]]

    def producer(batch: list[str]) -> None:
        for msg in batch:
            queue.put(LoggerRecord.create(msg, level=LogLevel.INFO))

    threads = [threading.Thread(target=producer, args=(batch,)) for batch in messages]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    listener.stop()

    emitted_messages = [record["msg"] for record in handler.emitted]
    assert sorted(emitted_messages) == sorted(msg for batch in messages for msg in batch)
    assert errors == []
