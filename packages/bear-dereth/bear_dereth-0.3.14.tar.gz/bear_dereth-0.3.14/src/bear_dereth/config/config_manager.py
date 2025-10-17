"""Config Manager Module for Bear Dereth."""

from contextlib import suppress
from functools import cached_property
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from bear_dereth.config.dir_manager import DirectoryManager
from bear_dereth.files.toml.file_handler import TomlFileHandler
from bear_dereth.stringing.manipulation import slugify


class Sources(BaseModel):
    """Model to represent configuration sources for debugging purposes."""

    files_loaded: list[dict[str, Any]] = []
    files_searched: list[Path] = []
    env_vars_used: list[str] = []
    final_merge_order: list[str] = []


class ConfigManager[ConfigType: BaseModel]:
    """A generic configuration manager with environment-based overrides.

    Configuration loading precedence (later sources override earlier):
    1. default.toml
    2. {env}.toml (e.g., dev.toml, prod.toml)
    3. local.toml
    4. Environment variables (prefixed with PROGRAM_NAME_)

    Searches in: ~/.config/{project_name}/ and ./config/{project_name}
    """

    def __init__(
        self,
        config_model: type[ConfigType],
        program_name: str,
        config_paths: list[Path] | None = None,
        file_names: list[str] | None = None,
        env: str = "dev",
    ) -> None:
        """Initialize the ConfigManager with a Pydantic model and configuration path.

        Args:
            config_model: A Pydantic model class defining the configuration schema.
            program_name: The name of the program (used for env var prefix and directory names).
            config_paths: Optional list of specific config file paths to use, must use full paths.
            file_names: Optional list of config file names to look for in order of precedence.
            env: The current environment (e.g., 'dev', 'prod') to determine which config files to load.
        """
        self._model: type[ConfigType] = config_model
        self._env: str = env
        self._program_name: str = program_name
        self._dir_manager = DirectoryManager(self.program_name.lower())
        self._default_files: list[str] = file_names or ["default.toml", f"{env}.toml", "local.toml"]
        self._config_paths: list[Path] = config_paths or self._default_paths(self._default_files)
        self._config: ConfigType | None = None

    @cached_property
    def program_name(self) -> str:
        """Get the normalized program name as uppercase with underscores."""
        return slugify(self._program_name, "_")

    @cached_property
    def prefix(self) -> str:
        """Get the environment variable prefix."""
        return f"{self.program_name}_".upper()

    @cached_property
    def resolved_config_paths(self) -> list[Path]:
        """Get the actual config files that exist and will be loaded."""
        return [path for path in self._config_paths if path.exists()]

    def _default_paths(self, file_names: list[str]) -> list[Path]:
        """Create default configuration paths based on the project name."""
        default_paths: list[Path] = [self._dir_manager.config(), self._dir_manager.local_config()]
        return [path.expanduser().resolve() / file_name for path in default_paths for file_name in file_names]

    def _get_env_overrides(self) -> dict[str, Any]:
        """Convert environment variables to nested dictionary structure.

        Convert variables like MY_APP_DATABASE_HOST to {'database': {'host': value}}.
        Only variables starting with the program prefix are considered.

        Returns:
            A nested dictionary representing environment variable overrides.
        """
        env_config: dict[str, Any] = {}

        for key, value in os.environ.items():
            if not key.startswith(self.prefix):
                continue

            clean_key: str = key[len(self.prefix) :].lower()
            parts: list[str] = clean_key.split("_")

            current: dict[str, Any] = env_config
            for part in parts[:-1]:
                current = current.setdefault(part, {})

            final_value: Any = self._convert_env_value(value)
            current[parts[-1]] = final_value
        return env_config

    def _convert_env_value(self, value: str) -> Any:
        """Convert string environment variables to appropriate types.

        Handles booleans, integers, floats, lists (comma-separated), and strings.

        Args:
            value: The string value from the environment variable.

        Returns:
            The value converted to the appropriate type.
        """
        if value.lower() in ("true", "false"):
            return value.lower() == "true"

        with suppress(ValueError):
            if "." in value:
                return float(value)

        if value.isdigit():
            return int(value)

        if "," in value:
            return [item.strip() for item in value.split(",")]

        return value

    def _load_toml_file(self, file_path: Path) -> dict[str, Any]:
        """Load a TOML file and return its contents using fluent TOML handler.

        Args:
            file_path: Path to the TOML file.

        Returns:
            A dictionary with the contents of the TOML file.
            Returns empty dict if file doesn't exist.

        Raises:
            ValueError: If the TOML file has invalid syntax.
        """
        if not file_path.exists() or not file_path.is_file():
            return {}
        try:
            return TomlFileHandler(file_path).read()
        except ValueError as e:
            raise ValueError(f"Invalid TOML syntax in {file_path}: {e}") from e

    def _get_relevant_config_files(self) -> list[Path]:
        """Get config files in loading order for current environment."""
        file_order: list[str] = self._default_files
        relevant_files: list[Path] = []
        for file_name in file_order:
            for path in [p for p in self._config_paths if p.name == file_name]:
                relevant_files.append(path)
        return relevant_files

    def config_sources(self) -> Sources:
        """Get detailed information about config sources and their contribution.

        This is here for debugging purposes.

        Returns:
            A Sources object detailing the configuration sources.
        """
        sources = Sources(files_searched=self._config_paths.copy())
        for path in sources.files_searched:
            data: dict[str, Any] = self._load_toml_file(path)
            if data:
                sources.files_loaded.append({"path": str(path), "keys": list(data.keys())})
                sources.final_merge_order.append(str(path))
        env_overrides: dict[str, Any] = self._get_env_overrides()
        if env_overrides:
            sources.env_vars_used = [key for key in os.environ if key.startswith(self.prefix)]
            sources.final_merge_order.append("environment_variables")
        return sources

    def _deep_merge(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Deep merge two dictionaries."""
        result: dict[str, Any] = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    @cached_property
    def load(self) -> ConfigType:
        """Load configuration from files and environment variables."""
        config_data: dict[str, Any] = {}
        for config_file in self.resolved_config_paths:
            file_data: dict[str, Any] = self._load_toml_file(config_file)
            if file_data:
                config_data = self._deep_merge(config_data, file_data)
        env_overrides: dict[str, Any] = self._get_env_overrides()
        if env_overrides:
            config_data = self._deep_merge(config_data, env_overrides)
        try:
            return self._model.model_validate(config_data)
        except ValidationError as e:
            raise ValueError(f"Configuration validation failed: {e}") from e

    @property
    def config(self) -> ConfigType:
        """Get the loaded configuration."""
        if self._config is None:
            self._config = self.load
        return self._config

    def reload(self) -> ConfigType:
        """Force reload the configuration."""
        attrs_to_check: list[str] = ["load", "_config_attrs", "resolved_config_paths"]
        for attr in attrs_to_check:
            if hasattr(self, attr):
                delattr(self, attr)
        self._config = None
        return self.config

    def create_default_config(self, target_path: Path | None = None) -> None:
        """Create a default config file with example values."""
        if not self._config_paths:
            return
        default_path: Path = target_path or self._dir_manager.local_config() / "default.toml"
        if not default_path.exists():
            default_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                with TomlFileHandler(default_path) as toml_handler:
                    toml_handler.write(self.config.model_dump(exclude_none=True))
            except Exception as e:
                raise OSError(f"Failed to create default config at {default_path}: {e}") from e

    @cached_property
    def _config_attrs(self) -> dict[str, Any]:
        """Cache all non-private attributes once."""
        return {attr: getattr(self.config, attr) for attr in dir(self.config) if not attr.startswith(("_", "model_"))}

    def has_config[T](self, config_type: type[T]) -> bool:
        """Check if the current configuration has an attribute or nested class of the given type."""
        type_name: str = config_type.__name__.lower()
        return any(attr == type_name or isinstance(value, config_type) for attr, value in self._config_attrs.items())

    def get_config[T](self, config_type: type[T]) -> T | None:
        """Get the configuration of the specified type if it exists."""
        type_name: str = config_type.__name__.lower()
        for attr, value in self._config_attrs.items():
            if attr == type_name or isinstance(value, config_type):
                return value
        return None


__all__ = ["ConfigManager", "Sources"]


# if __name__ == "__main__":
#     # Example usage and models
#     class DatabaseConfig(BaseModel):
#         """Configuration for an example database connection."""

#         host: str = "localhost"
#         port: int = 5432
#         username: str = "app"
#         password: str = "secret"
#         database: str = "myapp"

#     class LoggingConfig(BaseModel):
#         """Configuration for an example logging setup."""

#         level: str = "INFO"
#         format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
#         file: str | None = None

#         _validate_file: Callable[..., str | None] = nullable_string_validator("file")

#     class AppConfig(BaseModel):
#         """Example application configuration model."""

#         database: DatabaseConfig = DatabaseConfig()
#         logging: LoggingConfig = LoggingConfig()
#         environment: str = "development"
#         debug: bool = False
#         api_key: str = "your-api-key-here"
#         allowed_hosts: list[str] = ["localhost", "127.0.0.1"]

#     def get_config_manager(env: str = "dev") -> ConfigManager[AppConfig]:
#         """Get a configured ConfigManager instance."""
#         return ConfigManager[AppConfig](
#             config_model=AppConfig,
#             program_name="_test_app",
#             file_names=["default.toml", "development.toml", "local.toml"],
#             env=env,
#         )

#     config_manager: ConfigManager[AppConfig] = get_config_manager("dev")
#     config_manager.create_default_config()
#     config: AppConfig = config_manager.config

#     print(f"Database host: {config.database.host}")
#     print(f"Database port: {config.database.port}")
#     print(f"Debug mode: {config.debug}")
#     print(f"Environment: {config.environment}")

#     if config_manager.has_config(LoggingConfig):
#         logging_config: LoggingConfig | None = config_manager.get_config(LoggingConfig)
#         if logging_config is not None:
#             print(f"Logging level: {logging_config.level}")
