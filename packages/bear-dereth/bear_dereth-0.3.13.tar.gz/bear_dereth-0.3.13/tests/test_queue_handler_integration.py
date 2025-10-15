"""Integration tests for QueueHandler and QueueListener."""

from pathlib import Path
import time

import pytest

from bear_dereth.logger import LogLevel
from bear_dereth.logger.handlers.console_handler import ConsoleHandler
from bear_dereth.logger.handlers.file_handler import FileHandler
from bear_dereth.logger.handlers.queue_handler import QueueHandler
from bear_dereth.logger.handlers.queue_listener import QueueListener
from bear_dereth.logger.rich_printer import BearLogger


@pytest.fixture
def tmp_logger():
    """Fixture to provide a temporary BearLogger instance."""
    logger = BearLogger(name="test_logger")
    yield logger
    logger.clear_handlers()
    logger.close()


class TestQueueHandlerIntegration:
    """Test QueueHandler and QueueListener integration."""

    def test_queue_handler_creation(self, tmp_logger: BearLogger):
        """Test that QueueHandler can be created with proper DI."""
        tmp_logger.clear_handlers()
        queue_handler = QueueHandler()

        assert queue_handler.name == "queue"
        assert queue_handler.queue is not None
        assert queue_handler.caller is not None  # QueueListener
        assert hasattr(queue_handler.caller, "start")
        assert hasattr(queue_handler.caller, "stop")

    def test_queue_handler_with_target_handlers(self, tmp_logger: BearLogger):
        """Test QueueHandler with target handlers."""
        tmp_logger.clear_handlers()
        console_handler: ConsoleHandler = ConsoleHandler()
        queue_handler = QueueHandler(handlers=[console_handler])
        listener: QueueListener = queue_handler.caller
        assert len(listener.handlers) == 1
        assert listener.handlers[0] == console_handler
        assert len(queue_handler.caller.handlers) == 1

    # FIXME: This test intermittently fails with:
    # +  where '' = CaptureResult(out='', err='(\'Error enqueuing log record\', \'related_name=queue caller_function=test_queue_handler_logger_integration code_context=tmp_logger.info("Queue test message") filename=test_queue_handler_integration.py line_number=63 error_class=AttributeError error_text=\\\'\\\'Provide\\\' object has no attribute \\\'put_nowait\\\'\\\'\')\n(\'Error enqueuing log record\', \'related_name=queue caller_function=test_queue_handler_logger_integration code_context=tmp_logger.warning("Queue warning message") filename=test_queue_handler_integration.py line_number=64 error_class=AttributeError error_text=\\\'\\\'Provide\\\' object has no attribute \\\'put_nowait\\\'\\\'\')\n').out
    def test_queue_handler_logger_integration(self, capsys: pytest.CaptureFixture[str], tmp_logger: BearLogger):
        """Test QueueHandler integration with BearLogger."""
        tmp_logger.clear_handlers()

        console_handler = ConsoleHandler()
        queue_handler = QueueHandler(handlers=[console_handler])
        tmp_logger.add_handler(queue_handler)

        listener: QueueListener = queue_handler.caller
        assert listener is not None
        listener.start()

        try:
            tmp_logger.info("Queue test message")
            tmp_logger.warning("Queue warning message")

            # Give queue time to process
            time.sleep(0.1)

            # Check output
            captured = capsys.readouterr()
            assert "Queue test message" in captured.out
            assert "Queue warning message" in captured.out

        finally:
            # Always stop the listener
            queue_handler.caller.stop()

    def test_queue_handler_file_integration(self, tmp_path: Path) -> None:
        """Test QueueHandler with FileHandler target."""
        logger = BearLogger(name="file_test_logger")
        log_file: Path = tmp_path / "queue_test.log"

        logger.clear_handlers()

        # Create queue handler with file target
        file_handler = FileHandler(file_path=log_file)
        queue_handler = QueueHandler(handlers=[file_handler])
        logger.add_handler(queue_handler)

        # Start queue listener
        queue_handler.caller.start()

        try:
            # Send messages
            logger.info("Queued file message")
            logger.error("Queued error message")

            # Give queue time to process
            time.sleep(0.1)

            # Check file contents
            assert log_file.exists()
            content = log_file.read_text()
            assert "Queued file message" in content
            assert "Queued error message" in content

        finally:
            # Always stop the listener
            queue_handler.caller.stop()

    # FIXME: Investigate why this fails intermittently
    def test_queue_handler_multiple_targets(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str], tmp_logger: BearLogger
    ):
        """Test QueueHandler with multiple target handlers."""
        log_file: Path = tmp_path / "multi_queue_test.log"
        tmp_logger.clear_handlers()

        # Create queue handler with multiple targets
        console_handler = ConsoleHandler()
        file_handler = FileHandler(file_path=log_file)
        queue_handler = QueueHandler(handlers=[console_handler, file_handler])
        tmp_logger.add_handler(queue_handler)

        # Start queue listener
        queue_handler.caller.start()

        try:
            # Send message
            tmp_logger.warning("Multi-target queue message")

            # Give queue time to process
            time.sleep(0.1)

            # Check both console and file output
            captured = capsys.readouterr()
            assert "Multi-target queue message" in captured.out

            assert log_file.exists()
            file_content = log_file.read_text()
            assert "Multi-target queue message" in file_content

        finally:
            # Always stop the listener
            queue_handler.caller.stop()

    # TODO: Investigate why this fails intermittently
    def test_queue_handler_level_filtering(self, capsys: pytest.CaptureFixture[str], tmp_logger: BearLogger):
        """Test that QueueHandler respects log levels."""
        tmp_logger.clear_handlers()

        # Create queue handler with WARNING level
        console_handler = ConsoleHandler()
        queue_handler = QueueHandler(handlers=[console_handler], level=LogLevel.WARNING)
        tmp_logger.add_handler(queue_handler)

        # Start queue listener
        queue_handler.caller.start()

        try:
            # Send messages at different levels
            tmp_logger.debug("Debug message")  # Should be filtered out
            tmp_logger.info("Info message")  # Should be filtered out
            tmp_logger.warning("Warning message")  # Should pass through
            tmp_logger.error("Error message")  # Should pass through

            # Give queue time to process
            time.sleep(0.1)

            # Check output
            captured = capsys.readouterr()
            assert "Debug message" not in captured.out
            assert "Info message" not in captured.out
            assert "Warning message" in captured.out
            assert "Error message" in captured.out

        finally:
            # Always stop the listener
            queue_handler.caller.stop()

    def test_queue_listener_context_manager(self, capsys: pytest.CaptureFixture[str]):
        """Test QueueListener as context manager."""
        logger = BearLogger(name="context_test")
        logger.clear_handlers()

        console_handler = ConsoleHandler()
        queue_handler = QueueHandler(handlers=[console_handler])
        logger.add_handler(queue_handler)

        # Use QueueListener as context manager
        with queue_handler.caller:
            logger.info("Context manager test message")
            time.sleep(0.1)  # Give queue time to process

        # Check output
        captured = capsys.readouterr()
        assert "Context manager test message" in captured.out
