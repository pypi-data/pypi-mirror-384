"""Configuration for the pytest test suite."""

from collections.abc import Generator
from os import environ
from pathlib import Path
from typing import Any

import pytest

from bear_dereth import METADATA
from bear_dereth.logger.core.config import LoggerConfig

environ[f"{METADATA.env_variable}"] = "test"
from bear_dereth.di import Provide
from bear_dereth.logger import BearLogger


@pytest.fixture
def bear_logger() -> BearLogger:
    """Fixture for a BearLogger instance."""
    return BearLogger(name="test_handler")


@pytest.fixture
def tmp_test_logger() -> Generator[BearLogger[Any], Any]:
    """Fixture to provide a temporary BearLogger instance."""
    logger: BearLogger = BearLogger(name="test_logger")
    yield logger
    logger.clear_handlers()
    logger.close()


@pytest.fixture
def tmp_logger() -> BearLogger:
    return BearLogger(name=None, level="DEBUG", width=None)


@pytest.fixture
def tmp_logger_config() -> LoggerConfig:
    return LoggerConfig()


@pytest.fixture
def temp_file_with_text(tmp_path: Path) -> Path:
    """Create a temporary file for testing."""
    file: Path = tmp_path / "test_file.txt"
    file.write_text("Hello, World!")
    return file


@pytest.fixture
def nonexistent_file(tmp_path: Path) -> Path:
    """Path to a file that doesn't exist."""
    return tmp_path / "nonexistent.txt"


@pytest.fixture(autouse=True)
def reset_di_global_state() -> Generator[None, Any]:
    """Reset DI system global state before and after each test."""
    # Import the real logger container that should be the default
    from bear_dereth.logger.core.config import container as real_container  # noqa: PLC0415

    original_container: Any = getattr(Provide, "_container", None)

    yield

    # Always restore to the real logger container
    # This ensures logger tests work after DI tests
    Provide.set_container(real_container)


@pytest.fixture
def sample_string_data() -> dict[str, tuple[tuple[str, str], ...]]:
    # fmt: off
    return {
        "ints": (("1", "int"), ("2", "int"), ("3", "int")),
        "floats": (("1.0", "float"), ("2.0", "float"), ("3.0", "float")),
        "strings": (("'a'", "str"), ("'b'", "str"), ("'c'", "str")),
        "bools": (("True", "bool"), ("False", "bool"), ("true", "bool"), ("false", "bool")),
        "empty_data": (("[]", "list"), ("{}", "dict"), ("()", "tuple")),
        "lists": (("[1, 2]", "list[int]"), ("['a', 'b']", "list[str]"), ("[True, False]", "list[bool]")),
        "dicts": (("{'a': 1}", "dict[str, int]"), ("{'b': 2}", "dict[str, int]"), ("{'c': 3}", "dict[str, int]")),
        "tuples": (("(1, 2)", "tuple[int, ...]"),("('a', 'b')", "tuple[str, ...]"),("(True, False)", "tuple[bool, ...]")),
        "mixed_tuples": (("(1, 'a')", "tuple[int, str]"), ("(True, 2.0)", "tuple[bool, float]")),
        "mixed_lists": (("[1, 'a']", "list[int | str]"), ("[True, 2.0]", "list[bool | float]")),
        "mixed_dicts": (("{'a': 1, 'b': 'two'}", "dict[str, int | str]"),("{'key': True, 'value': 3.14}", "dict[str, bool | float]")),
        "mixed_sets": (("{1, 'a'}", "set[int | str]"), ("{True, 2.0}", "set[bool | float]")),
        "bytes": (("b'hello'", "bytes"), ("b'world'", "bytes")),
        "sets": (("{1, 2}", "set[int]"), ("{'a', 'b'}", "set[str]"), ("{True, False}", "set[bool]")),
        "none": (("None", "NoneType"),),
        "path": (("/Users/chaz/Documents", "path"), (str(Path("/Users/chaz/Downloads")), "path")),
    }
    # fmt: on
