"""Extended test cases for BearLogger system."""

from pathlib import Path
from typing import Any, NoReturn, TextIO

from _pytest.capture import CaptureResult
import pytest
from rich.status import Status

from bear_dereth.logger import BearLogger, ConsoleHandler, FileHandler
from bear_dereth.logger.common import LogLevel
from bear_dereth.logger.core.config import ConsoleOptions, LoggerConfig, LoggerTheme
from bear_dereth.logger.protocols import Handler


@pytest.fixture
def logger() -> BearLogger[Any]:
    """Fixture for a BearLogger instance."""
    return BearLogger(name="test_handler")


class TestBearLoggerHandlerManagement:
    """Test handler management functionality."""

    def test_add_remove_handlers(self, logger: BearLogger[Any]):
        """Test adding and removing handlers."""
        initial_count = len(logger.handlers)

        # Add a new handler
        new_handler = ConsoleHandler(name="test_handler")
        assert new_handler.console_options is not None, "ConsoleOptions must be provided via DI or directly."
        assert isinstance(new_handler.console_options, ConsoleOptions), "console_options must be ConsoleOptions"
        assert callable(new_handler.error_callback), "error_callback must be callable"
        assert callable(new_handler.get_level), "root_level must be callable and return a LogLevel"

        logger.add_handler(new_handler)

        assert len(logger.handlers) == initial_count + 1
        assert new_handler in logger.handlers

        # Remove the handler
        logger.remove_handler(new_handler)
        assert len(logger.handlers) == initial_count
        assert new_handler not in logger.handlers

    def test_add_duplicate_handler(self, logger: BearLogger[Any]):
        """Test that adding the same handler twice doesn't create duplicates."""
        handler: ConsoleHandler[TextIO] = ConsoleHandler(name="duplicate_test")

        logger.add_handler(handler)
        initial_count = len(logger.handlers)

        logger.add_handler(handler)  # Add same handler again
        assert len(logger.handlers) == initial_count  # Should not increase

    def test_clear_handlers(self, logger: BearLogger[Any]):
        """Test clearing all handlers."""
        logger.clear_handlers()
        logger.add_handler(ConsoleHandler(name="test1"))
        logger.add_handler(ConsoleHandler(name="test2"))

        assert logger.has_handlers()
        assert len(logger.handlers) == 2
        logger.clear_handlers()

        assert not logger.has_handlers()
        assert len(logger.handlers) == 0

    def test_has_handlers(self, logger: BearLogger[Any]):
        """Test has_handlers method."""
        assert logger.has_handlers()
        logger.clear_handlers()
        assert not logger.has_handlers()


class TestBearLoggerFileLogging:
    """Test file logging functionality."""

    def test_file_handler_integration(self, tmp_path: Path):
        """Test that file handler works with BearLogger."""
        log_file: Path = Path(tmp_path) / "test.log"

        logger: BearLogger[Any] = BearLogger(name="file_test")
        file_handler = FileHandler(file_path=log_file, level=LogLevel.DEBUG)
        logger.add_handler(file_handler)

        logger.info("File test message")
        logger.error("File error message")

        assert log_file.exists()
        content: str = log_file.read_text()
        assert "File test message" in content
        assert "File error message" in content

    def test_multiple_file_handlers(self, tmp_path: Path):
        """Test multiple file handlers writing to different files."""
        log_file1: Path = tmp_path / "app.log"
        log_file2: Path = tmp_path / "error.log"

        logger = BearLogger(name="multi_file")
        logger.clear_handlers()
        logger.add_handler(FileHandler(file_path=log_file1))
        logger.add_handler(FileHandler(file_path=log_file2))

        logger.warning("Multi-file test")

        # Both files should have the message
        assert "Multi-file test" in log_file1.read_text()
        assert "Multi-file test" in log_file2.read_text()


class TestBearLoggerConfiguration:
    """Test configuration and theming."""

    def test_custom_config(self):
        """Test BearLogger with custom config."""
        custom_theme = LoggerTheme(info="green", error="bright_red bold", debug="dim cyan")
        custom_config = LoggerConfig(theme=custom_theme)

        logger = BearLogger(config=custom_config)

        # Check that custom theme is applied
        assert logger.config.theme.info == "green"
        assert logger.config.theme.error == "bright_red bold"
        assert logger.config.theme.debug == "dim cyan"

    def test_console_options_integration(self):
        """Test ConsoleOptions integration."""
        console_opts = ConsoleOptions(width=80, no_color=True, markup=False)

        logger = BearLogger(name="console_opts", console_options=console_opts)

        # Verify console options were applied
        assert logger._console.options.max_width == 80  # type: ignore[attr-defined]
        # Note: no_color and markup are harder to test directly

    def test_log_levels(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test different log levels."""
        logger: BearLogger[TextIO] = BearLogger(level=LogLevel.WARNING)

        assert logger.level == LogLevel.WARNING

        logger.set_level(LogLevel.INFO)
        assert logger.level == LogLevel.INFO

        logger.info("This message should be output.")
        logger.debug("This message should not be output.")
        captured: CaptureResult[str] = capsys.readouterr()
        print(captured.out)
        # assert "this message should be output" in captured.out.lower()
        # assert "this message should not be output" not in captured.out.lower()


class TestBearLoggerRichIntegration:
    """Test Rich library integration features."""

    def test_print_json(self, capsys: pytest.CaptureFixture[str]):
        """Test JSON printing functionality."""
        logger = BearLogger(name="json_test")

        test_data = {"name": "test", "value": 42}
        logger.print_json(data=test_data)

        captured = capsys.readouterr()
        assert "test" in captured.out
        assert "42" in captured.out

    def test_inspect_object(self, capsys):
        """Test object inspection functionality."""
        logger = BearLogger(name="inspect_test")

        test_obj = {"key": "value", "number": 123}
        logger.inspect(test_obj)

        captured = capsys.readouterr()
        # Rich inspect should show object details
        assert captured.out  # Should have some output

    def test_status_context_manager(self, logger: BearLogger[Any]):
        """Test status context manager."""
        with logger.status("Processing...") as status:
            assert status is not None
            assert isinstance(status, Status)

    def test_log_with_rich_formatting(self, capsys):
        """Test log method with Rich console.log()."""
        logger = BearLogger(name="rich_log", width=80)

        logger.log("Test log message", style="bold blue")

        captured = capsys.readouterr()
        assert "Test log message" in captured.out


class TestBearLoggerContextManager:
    """Test context manager functionality."""

    def test_context_manager_usage(self, tmp_path: Path) -> None:
        """Test BearLogger as context manager."""
        log_file = tmp_path / "context_test.log"

        # Create logger without default handlers to avoid closing stdout/stderr
        logger = BearLogger(name="context_test")
        logger.clear_handlers()  # Remove default ConsoleHandler

        with logger:
            logger.add_handler(FileHandler(file_path=log_file))
            logger.info("Context manager test")

        # After exit, handlers should be closed
        # File should still exist and have content
        assert log_file.exists()
        assert "Context manager test" in log_file.read_text()

    def test_context_manager_cleanup(self, tmp_path: Path):
        """Test that context manager properly cleans up resources."""
        logger = BearLogger(name="cleanup_test", width=None)
        logger.clear_handlers()

        log_file: Path = tmp_path / "cleanup_test.log"
        handler = FileHandler(file_path=log_file)
        logger.add_handler(handler)

        with logger:
            logger.info("Inside context")

        # Context manager should have called close() on handlers
        # Verify the log file was created and has content
        assert log_file.exists()
        assert "Inside context" in log_file.read_text()


class TestBearLoggerErrorHandling:
    """Test error handling and edge cases."""

    def test_error_callback(self, logger: BearLogger[Any], capsys: pytest.CaptureFixture[str]) -> None:
        """Test error callback functionality."""

        class FailingHandler(Handler):
            def __init__(self) -> None:
                self.name = "failing_handler"
                self.file = None
                self.caller = None

            def emit(self, msg, style, level, **kwargs) -> NoReturn:  # noqa: ARG002
                """Simulate a failure in the handler."""
                raise ValueError("Test error")

            def close(self) -> None:
                pass

            def flush(self) -> None:
                pass

        logger.clear_handlers()
        failing_handler = FailingHandler()
        logger.add_handler(failing_handler)

        with pytest.raises(ValueError, match="Test error"):
            failing_handler.emit("This will fail", "error", level=LogLevel.ERROR)

        logger.info("This should trigger error callback")
        captured: CaptureResult[str] = capsys.readouterr()
        assert "test error" in captured.err.lower()

    def test_empty_handlers_list(self, logger: BearLogger[Any]):
        """Test behavior with no handlers."""
        logger.clear_handlers()

        # Should not crash
        logger.info("This message goes nowhere")

        assert not logger.has_handlers()


class TestBearLoggerDynamicMethods:
    """Test dynamically created logging methods."""

    def test_all_dynamic_methods_exist(self):
        """Test that all expected dynamic methods are created."""
        logger = BearLogger(name="dynamic_test")

        expected_methods = ["info", "warning", "error", "debug", "success", "failure", "exception"]

        for method_name in expected_methods:
            assert hasattr(logger, method_name)
            method = getattr(logger, method_name)
            assert callable(method)

    def test_dynamic_methods_call_handlers(self, capsys: pytest.CaptureFixture[str]):
        """Test that dynamic methods actually call handlers."""
        logger = BearLogger(name="dynamic_call_test")
        logger.info("Info test")
        logger.warning("Warning test")
        logger.error("Error test")

        captured: CaptureResult[str] = capsys.readouterr()
        assert "Info test" in captured.out
        assert "Warning test" in captured.out
        assert "Error test" in captured.out
