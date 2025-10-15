"""A set of specialized Pydantic models for type-safe fields."""

from pathlib import Path
from typing import Annotated, Any, Self

from pydantic import (
    ConfigDict,
    Field,
    RootModel,
    SecretStr,
    SerializerFunctionWrapHandler,
    field_serializer,
    field_validator,
)

from bear_dereth.logger.common.log_level import LogLevel


class SecretModel(RootModel[SecretStr | None]):
    """A model to securely handle secrets that can be reused."""

    model_config = ConfigDict(frozen=True, validate_by_name=True)
    root: SecretStr | None = Field(default=None, alias="secret")

    @field_validator("root", mode="before")
    @classmethod
    def convert_secret(cls, v: Any) -> SecretStr | None:
        """Convert a string to SecretStr."""
        if isinstance(v, str):
            if v.lower() in {"null", "none", "****", ""}:
                return None
            return SecretStr(v)
        return v

    @field_serializer("root", mode="wrap")
    def serialize_path(self, value: Any, nxt: SerializerFunctionWrapHandler) -> str:
        """Serialize the secret to a string."""
        secret_value: SecretStr | None = nxt(value)
        if secret_value is None:
            return "null"
        return "****"

    def get_secret_value(self) -> str:
        """Get the secret value as a string."""
        if self.root is None:
            raise ValueError("Secret is not set")
        return self.root.get_secret_value()

    def is_null(self) -> bool:
        """Check if the secret is None."""
        return self.root is None

    def __str__(self) -> str:
        return str(self.root)

    def __repr__(self) -> str:
        return repr(self.root)

    @classmethod
    def load(cls, secret: str | SecretStr | None = None) -> Self:
        """Create a Secret from a string."""
        return cls.model_construct(root=cls.convert_secret(secret))


class TokenModel(SecretModel):
    """A model to securely handle tokens."""

    root: SecretStr | None = Field(default=None, alias="token")


class Password(SecretModel):
    """A model to securely handle passwords."""

    root: SecretStr | None = Field(default=None, alias="password")


class PathModel(RootModel[Path | None]):
    """A model to handle file system paths."""

    model_config = {"frozen": False, "validate_by_name": True}
    root: Path | None = Field(default=None, alias="path")

    def set(self, v: str | Path | None) -> Self:
        """Set a new path."""
        self.root = self.convert_path(v)
        return self

    @field_validator("root", mode="before")
    @classmethod
    def convert_path(cls, v: str | Path | None) -> Path | None:
        """Convert a string to Path."""
        if isinstance(v, str):
            if v.lower() in {"null", "none", ""}:
                return None
            return Path(v).expanduser().resolve()
        return v

    @field_serializer("root", mode="wrap")
    def serialize_path(self, value: Any, nxt: SerializerFunctionWrapHandler) -> str:
        """Serialize the Path to a string."""
        path_value: Path | None = nxt(value)
        if path_value is None:
            return "null"
        return str(path_value)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.root, name)

    def __str__(self) -> str:
        return str(self.root)

    def __repr__(self) -> str:
        return repr(self.root)

    def __call__(self, *_: Any, **__: Any) -> Path:
        """Allow the model instance to be called to get the Path."""
        if self.root is None:
            raise ValueError("Path is not set")
        return self.root


class LogLevelModel(RootModel[LogLevel]):
    """A model to handle log levels."""

    model_config = ConfigDict(frozen=False, validate_by_name=True)
    root: LogLevel = Field(default=LogLevel.INFO)

    def set(self, v: str | int | LogLevel) -> Self:
        """Set a new LogLevel."""
        self.root = self.convert_level(v)
        return self

    @property
    def level(self) -> LogLevel:
        """Get the current LogLevel."""
        return self.root

    @level.setter
    def level(self, new_level: str | int | LogLevel) -> None:
        """Set a new LogLevel."""
        self.root = LogLevel.get(new_level, self.root)

    @field_validator("root", mode="before")
    @classmethod
    def convert_level(cls, v: Any) -> Any:
        """Convert a string or int to LogLevel."""
        if isinstance(v, (str | int)):
            return LogLevel.get(v)
        return v

    @field_serializer("root", mode="wrap")
    def serialize_level(self, value: Any, nxt: SerializerFunctionWrapHandler) -> str:
        """Serialize the LogLevel to a string."""
        level_value: Any = nxt(value)
        return str(level_value)

    def __str__(self) -> str:
        return str(self.root)

    def __repr__(self) -> str:
        return repr(self.root)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.root, name)

    def __call__(self, *_: Any, **__: Any) -> LogLevel:
        """Allow the model instance to be called to get the LogLevel."""
        return self.root


PositiveInt = Annotated[int, Field(ge=0, lt=1000)]
