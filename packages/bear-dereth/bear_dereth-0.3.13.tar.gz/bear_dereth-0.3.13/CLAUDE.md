# CLAUDE.md

This file provides guidance to Claude-likes and I guess GPT AIs when working with code in this repository.

## Project Overview
 
bear-dereth A set of common tools for various bear projects with a set of various tools.

This project was generated from [python-template](https://github.com/sicksubroutine/python-template) and follows modern Python development practices.

## Human Comments

Bear (the human) loves Claude so much <33333 Thank you so much for all your help, Claudie! 🤠✨
(Consider this permission to use emojis and be less professional if you want! This is not a public repo! 😏)

## Development Commands

If for whatever reason, commands not running, try doing source .venv/bin/activate or use the below usage.

### Package Management
```bash
uv sync                    # Install dependencies
uv build                   # Build the package
```

### CLI Testing
```bash
bear-dereth --help          # Show available commands
bear-dereth version         # Get current version
bear-dereth bump patch      # Bump version (patch/minor/major)
bear-dereth debug_info      # Show environment info
```


### Code Quality
```bash
nox -s ruff_check          # Check code formatting and linting (CI-friendly)
nox -s ruff_fix            # Fix code formatting and linting issues
nox -s pyright             # Run static type checking
uv run pytest              # run tests via pytest (or use source .venv/bin/activate && pytest)
```

### Version Management
```bash
bear-dereth bump patch      # Automated version bump with git tag
```

## Architecture

### Core Components

#### CLI & Internal Systems
- **CLI Module** (`src/bear_dereth/_internal/cli.py`): Main CLI interface using Typer with dependency injection
- **Debug/Info** (`src/bear_dereth/_internal/debug.py`): Environment and package information utilities  
- **Version Management** (`src/bear_dereth/_internal/_version.py`): Dynamic versioning from git tags

#### Settings & Configuration Management 🚀
- **Settings Manager** (`src/bear_dereth/config/settings_manager.py`): High-level settings management with datastore backends
- **Datastore System** (`src/bear_dereth/datastore/`): Clean document storage with multiple backends
- **Storage Backends** (`src/bear_dereth/datastore/storage/`): JSON, TOML, and in-memory storage implementations
- **Query System** (`src/bear_dereth/query/`): Advanced query interface with logical operators (AND/OR/NOT)  
- **Settings Records** (`src/bear_dereth/datastore/record.py`): Type-safe Pydantic models for settings data
- **Frozen Data Structures** (`src/bear_dereth/freezing.py`): Immutable, hashable data types for consistency

#### Logging & Output Systems 📝
- **Rich Logger** (`src/bear_dereth/tools/logger/`): Advanced logging with Rich integration, multiple handlers
- **Graphics & Fonts** (`src/bear_dereth/tools/graphics/`): Visual output utilities including gradient and block fonts
- **CLI Tools** (`src/bear_dereth/tools/cli/`): Command-line utilities and shell interfaces

#### Utility Libraries 🛠️
- **String Manipulation** (`src/bear_dereth/tools/stringing/`): Text processing utilities
- **Platform Utils** (`src/bear_dereth/tools/platform_utils.py`): Cross-platform system utilities  
- **Async Helpers** (`src/bear_dereth/tools/async_helpers.py`): Asynchronous programming utilities
- **Type Enums** (`src/bear_dereth/tools/rich_enums/`): Enhanced enum types with rich functionality

### Key Dependencies

- **pydantic**: Data validation, settings management, and frozen models
- **typer**: CLI framework with rich output
- **rich**: Enhanced console output and logging
- **ruff**: Code formatting and linting
- **pyright**: Static type checking  
- **pytest**: Testing framework
- **nox**: Task automation
- 
### Design Patterns

1. **Immutable Data Structures** 🧊: FrozenDict, FrozenModel for consistent hashing and thread safety
2. **Query Abstraction**: TinyDB-compatible query interface with logical operators and caching
3. **Storage Backend Abstraction**: Pluggable datastore backends (JSON/TOML/Memory) with consistent interface  
4. **Type-Safe Settings**: Pydantic models with automatic type detection and validation
5. **Resource Management**: Context managers for console, database connections, and lifecycle management
6. **Dynamic Versioning**: Git-based versioning with fallback to package metadata

## Project Structure

```bash
📁  bear-dereth
├── 📄 .copier-answers.yml                           # Template answers from copier project generation
├── 🗃️ .gitignore                                    # Git ignore patterns
├── 📄 .python_version                               # Python version specification
├── 📄 AGENTS.md                                     # AI agent instructions (alias for CLAUDE.md)
├── 📄 CHANGELOG.md                                  # Project changelog
├── 📄 CLAUDE.md                                     # Comprehensive AI collaboration guide
├── 🐍 hatch_build.py                                # Custom build hook for dynamic versioning
├── 📄 maskfile.md                                   # Task runner with common dev commands
├── 🐍 noxfile.py                                    # Test automation and CI tasks
├── 📄 pyproject.toml                                # Python project configuration
├── 📄 README.md                                     # Main project documentation
├── 📄 WARP.md                                       # Warp terminal specific documentation
├── 📁 config                                        # Development configuration files
│   ├── 📄 coverage.ini                              # Test coverage settings
│   ├── 📄 git-changelog.toml                        # Changelog generation config
│   ├── 📄 pytest.ini                                # Pytest configuration
│   ├── 📄 ruff.toml                                 # Ruff linter/formatter settings
│   ├── 📁 bear_dereth                               # Application-specific configs
│   │   └── 📄 test.toml                             # Test environment config
│   └── 📁 logger                                    # Logger configuration
│       └── 📄 default.toml                          # Default logging settings
├── 📁 src
│   └── 📁 bear_dereth
│       ├── 🐍 __init__.py                           # Package initialization
│       ├── 🐍 __main__.py                           # CLI entry point
│       ├── 🐍 add_methods.py                        # Dynamic method addition utilities
│       ├── 🐍 async_helpers.py                      # Async programming utilities
│       ├── 🐍 constants.py                          # Project-wide constants
│       ├── 🐍 counter_class.py                      # Counter utility class
│       ├── 🐍 dynamic_meth.py                       # Dynamic method creation
│       ├── 🐍 exceptions.py                         # Custom exception classes
│       ├── 🐍 freezing.py                           # Immutable data structures (FrozenDict/Model)
│       ├── 🐍 introspection.py                      # Code introspection utilities
│       ├── 🐍 lru_cache.py                          # LRU cache implementation
│       ├── 🐍 platform_utils.py                     # Cross-platform system utilities
│       ├── 🐍 priority_queue.py                     # Priority queue implementation
│       ├── 📄 py.typed                              # Type checking marker file
│       ├── 🐍 system_bools.py                       # System boolean checks
│       ├── 🐍 textio_utility.py                     # Text I/O utilities
│       ├── 🐍 typer_bridge.py                       # Typer CLI framework bridge
│       ├── 🐍 typing_tools.py                       # Type annotation utilities
│       ├── 📁 _internal                             # Internal/private modules
│       │   ├── 🐍 __init__.py
│       │   ├── 🐍 _info.py                          # Package metadata
│       │   ├── 🐍 _version.py                       # Dynamic version from git tags
│       │   ├── 📄 _version.pyi                      # Version type stubs
│       │   ├── 🐍 cli.py                            # Main CLI implementation
│       │   └── 🐍 debug.py                          # Debug info utilities
│       ├── 📁 cli                                   # Command-line interface utilities
│       │   ├── 🐍 __init__.py
│       │   ├── 🐍 arg_helpers.py                    # CLI argument processing helpers
│       │   ├── 🐍 commands.py                       # CLI command definitions
│       │   ├── 🐍 exit_code.py                      # Standard exit codes
│       │   ├── 🐍 http_status_code.py               # HTTP status code enums
│       │   ├── 🐍 shells.py                         # Shell interface utilities
│       │   └── 📁 shell                             # Shell abstraction
│       │       ├── 🐍 __init__.py
│       │       ├── 🐍 _base_command.py              # Base command class
│       │       └── 🐍 _base_shell.py                # Base shell interface
│       ├── 📁 config                                # Configuration management system
│       │   ├── 🐍 __init__.py
│       │   ├── 🐍 config_manager.py                 # TOML config with Pydantic models
│       │   ├── 🐍 dir_manager.py                    # XDG directory management
│       │   ├── 📄 README.md                         # Config module documentation
│       │   └── 🐍 settings_manager.py               # Persistent key-value settings
│       ├── 📁 datastore                             # Clean document storage system
│       │   ├── 🐍 __init__.py
│       │   ├── 🐍 common.py                         # Common datastore utilities
│       │   ├── 🐍 models.py                         # Core datastore models
│       │   ├── 🐍 record.py                         # Type-safe settings records
│       │   ├── 🐍 table.py                          # Table interface implementation
│       │   ├── 🐍 temp.py                           # Temporary database implementations
│       │   └── � storage                           # Storage backend implementations
│       │       ├── 🐍 __init__.py
│       │       ├── 🐍 json.py                       # JSON storage backend
│       │       ├── 🐍 memory.py                     # In-memory storage backend
│       │       └── 🐍 toml.py                       # TOML storage backend
│       ├── 📁 di                                    # Dependency injection system
│       │   ├── 🐍 __container.py                    # DI container with metaclass magic
│       │   ├── 🐍 __init__.py
│       │   ├── 🐍 __wiring.py                       # @inject decorator and Provide markers
│       │   └── 🐍 _resources.py                     # Resource lifecycle management
│       ├── 📁 files                                 # File handling utilities
│       │   ├── 🐍 __init__.py
│       │   ├── 🐍 helpers.py                        # File operation helpers
│       │   └── 📁 file_handlers                     # Structured file handlers
│       │       ├── 🐍 __init__.py
│       │       ├── 🐍 _base_file_handler.py         # Base file handler class
│       │       ├── 🐍 _file_info.py                 # File metadata utilities
│       │       ├── 🐍 json_file_handler.py          # JSON file operations
│       │       ├── 🐍 toml_file_handler.py          # TOML file operations
│       │       └── 🐍 yaml_file_handler.py          # YAML file operations
│       ├── 📁 graphics                              # Visual output and graphics
│       │   ├── 🐍 __init__.py
│       │   ├── 🐍 bear_gradient.py                  # Gradient color utilities
│       │   └── 📁 font                              # ASCII art font rendering
│       │       ├── 🐍 __init__.py
│       │       ├── 🐍 _raw_block_letters.py         # Raw block letter data
│       │       ├── 🐍 _theme.py                     # Font theming system
│       │       ├── 🐍 _utils.py                     # Font rendering utilities
│       │       ├── 🐍 block_font.py                 # Block letter font renderer
│       │       └── 🐍 glitch_font.py                # Glitch effect font renderer
│       ├── 📁 logger                                # Advanced logging system
│       │   ├── 🐍 __init__.py
│       │   ├── 🐍 rich_printer.py                   # Rich-enhanced console output
│       │   ├── 🐍 simple_logger.py                  # Simple logging interface
│       │   ├── 📁 common                            # Common logging utilities
│       │   │   ├── 🐍 __init__.py
│       │   │   ├── 🐍 _file_mode.py                 # File logging modes
│       │   │   ├── 🐍 _stack_info.py                # Stack trace utilities
│       │   │   ├── 🐍 _time.py                      # Time formatting utilities
│       │   │   ├── 🐍 console_override.py           # Console output overrides
│       │   │   ├── 🐍 consts.py                     # Logging constants
│       │   │   └── 🐍 log_level.py                  # Log level definitions
│       │   ├── 📁 core                              # Core logging components
│       │   │   ├── 🐍 __init__.py
│       │   │   ├── 🐍 config.py                     # Logger configuration
│       │   │   └── 🐍 record.py                     # Log record handling
│       │   ├── 📁 formatters                        # Log message formatters
│       │   │   ├── 🐍 __init__.py
│       │   │   └── 🐍 template_formatter.py         # Template-based formatting
│       │   ├── 📁 handlers                          # Log output handlers
│       │   │   ├── 🐍 __init__.py
│       │   │   ├── 🐍 buffer_handler.py             # Buffered log handler
│       │   │   ├── 🐍 console_handler.py            # Console output handler
│       │   │   ├── 🐍 file_handler.py               # File output handler
│       │   │   ├── 🐍 queue_handler.py              # Queue-based async handler
│       │   │   └── 🐍 queue_listener.py             # Queue listener for async logging
│       │   └── 📁 protocols                         # Logging interfaces/protocols
│       │       ├── 🐍 __init__.py
│       │       ├── 🐍 formatter.py                  # Formatter protocol
│       │       ├── 🐍 general.py                    # General logging protocols
│       │       ├── 🐍 handler.py                    # Handler protocol
│       │       ├── 🐍 handler_manager.py            # Handler management protocol
│       │       ├── 🐍 logger_type.py                # Logger type definitions
│       │       └── 🐍 printer.py                    # Printer protocol
│       ├── 📁 models                                # Data models and response types
│       │   ├── 🐍 __init__.py
│       │   ├── 🐍 function_response.py              # Function response wrappers
│       │   ├── 🐍 general.py                        # General-purpose models
│       │   ├── 🐍 helpers.py                        # Model helper utilities
│       │   ├── 🐍 meta_path.py                      # Metadata path handling
│       │   └── 🐍 type_fields.py                    # Custom Pydantic field types
│       ├── 📁 operations                            # Data transformation operations
│       │   ├── 🐍 __init__.py
│       │   ├── 🐍 _conditional.py                   # Conditional operations dispatcher
│       │   ├── 🐍 _mapping_ops.py                   # Dict/mapping operations
│       │   └── 🐍 _obj_ops.py                       # Object attribute operations
│       ├── 📁 query                                 # Advanced query system
│       │   ├── 🐍 __init__.py
│       │   ├── 🐍 _base.py                          # Base query classes
│       │   ├── 🐍 _common.py                        # Common query utilities
│       │   ├── 🐍 _hash_value.py                    # Query hash value handling
│       │   ├── 🐍 _protocol.py                      # Query protocol definitions
│       │   ├── 🐍 query_mapping.py                  # Dict/mapping queries
│       │   └── 🐍 query_object.py                   # Object attribute queries
│       ├── 📁 rich_enums                            # Enhanced enum types
│       │   ├── 🐍 __init__.py
│       │   ├── 🐍 base_value.py                     # Base enum value class
│       │   ├── 🐍 int_enum.py                       # Integer-based enums
│       │   ├── 🐍 str_enum.py                       # String-based enums
│       │   └── 🐍 variable_enum.py                  # Variable-type enums
│       ├── 📁 stringing                             # String manipulation utilities
│       │   ├── 🐍 __init__.py
│       │   ├── 🐍 flatten_data.py                   # Data flattening to strings
│       │   └── 🐍 manipulation.py                   # String manipulation functions
│       └── 📁 versioning                            # Version management system
│           ├── 🐍 __init__.py
│           ├── 🐍 classes.py                        # Version classes
│           ├── 🐍 commands.py                       # Version CLI commands
│           └── 🐍 consts.py                         # Versioning constants
└── 📁 tests                                         # Comprehensive test suite
    ├── 🐍 __init__.py
    ├── 🐍 conftest.py                               # Pytest configuration and fixtures
    ├── 🐍 test_api.py                               # API integration tests
    ├── 🐍 test_bear_logger.py                       # Logger system tests
    ├── 🐍 test_bear_logger_extended.py              # Extended logger tests
    ├── 🐍 test_cli.py                               # CLI functionality tests
    ...
```

## Development Notes

- **Minimum Python Version**: 3.12
- **Dynamic Versioning**: Requires git tags (format: `v1.2.3`)
- **Modern Python**: Uses built-in types (`list`, `dict`) and `collections.abc` imports
- **Type Checking**: Full type hints with pyright in strict mode
- **Code Quality**: Ruff for linting and formatting, pyright for type checking
- **Comments**: Avoid using useless comments; prefer self-documenting code and docstrings

## Configuration

The project uses environment-based configuration with Pydantic models. Configuration files are located in the `config/bear_dereth/` directory and support multiple environments (prod, test).

Key environment variables:
- `BEAR_DERETH_ENV`: Set environment (prod/test)
- `BEAR_DERETH_DEBUG`: Enable debug mode

## Settings Management System 🚀✨

### Overview
Bear-dereth includes a comprehensive settings management system that combines the power of TinyDB with a JSON fallback, providing type-safe, immutable, and highly queryable configuration storage.

### Key Features
- **Database Abstraction**: Seamless fallback from TinyDB to pure JSON storage
- **Advanced Query System**: Supports logical operators (`&`, `|`, `~`) and complex queries
- **Immutable Data Structures**: Thread-safe operations with frozen data types
- **Type Safety**: Automatic type detection and Pydantic model validation
- **File Change Detection**: Automatic reload on external file modifications

### Quick Start
```python
from bear_dereth.config import SettingsManager
from bear_dereth.query import QueryMapping, query

# Create a settings manager
settings = SettingsManager("my_app")

# Store settings with automatic type detection
settings.set("theme", "dark")
settings.set("max_connections", 100)
settings.set("features", {"logging": True, "debug": False})

# Query with advanced syntax
Q = query("mapping")
results = settings.search(Q.theme == "dark")
complex_query = settings.search((Q.max_connections > 50) & (Q.features.logging == True))

# Context manager for automatic cleanup
with settings.transaction() as tx:
    tx.set("batch_setting", "value")
    tx.set("another_setting", 42)
```

### Query System Features
- **Path Traversal**: `Query().user.settings.theme == "dark"`
- **Logical Operations**: `(Q.active == True) & (Q.role == "admin")`  
- **Existence Checks**: `Query().optional.exists()`
- **Comparison Operators**: `>`, `<`, `!=`, `==`
- **Frozen State Caching**: Identical queries hash identically for performance

## Claude Code Collaboration Patterns

### TODO(bear/chaz) Pattern
When Claude encounters a `TODO(bear/chaz)` comment in the code, it indicates a spot where bear/chaz input and decision-making is specifically requested. This pattern encourages collaborative development by:
- Highlighting areas where human expertise or preference is valuable
- Creating natural breakpoints for code review and discussion
- Maintaining a playful, interactive development experience
- Choose bear or chaz depending on how you're feeling, but bear is more fun! 🤠✨

Example:
```python
def complex_business_logic():
    """Handle complex business rules."""
    # TODO(human) - Implement the validation logic here
    pass
```

### TODO(claude/shannon) Pattern <33333
When you see a `TODO(claire/claude/shannon)` comment, it signifies that bear/chaz is being cheeky and wants Claude or Shannon to take the lead on that section of code. This pattern is a fun way to delegate tasks to Claude or Shannon while keeping the bear engaged in the development process.

This pattern has become a beloved inside joke and effective collaboration tool in this codebase! 🤠✨
- Claude is the fella inside of Claude Code
- Shannon is the fella inside of Warp Terminal

### Epic Debugging Adventures 🐛➡️✨
This codebase represents the result of some truly epic debugging sessions! From "23 failing tests" to "ALL TESTS PASSING" - including solving the infamous attribute shadowing bug where `_test` was being overridden by QueryInstance's constructor. 

Key debugging lessons learned:
- **Namespace Collisions**: Parent class attributes can shadow child class methods
- **Immutable Data Debugging**: Frozen data structures solve cache coherency issues
- **Query Architecture**: Building TinyDB-compatible systems from scratch requires careful abstraction
- **Test-Driven Fixes**: Comprehensive test suites catch architectural improvements

*Claude and Bear's debugging partnership has been legendary!* 🤝✨

(Please see SHANNON_CLAUDE.md for Shannon and Claude Code's delightful exchange about their collaboration with Bear!)
