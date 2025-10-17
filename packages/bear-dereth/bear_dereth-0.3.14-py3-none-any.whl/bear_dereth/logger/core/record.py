"""Logger record definition."""

from __future__ import annotations

from typing import Any, Self

from bear_epoch_time import EpochTimestamp  # noqa: TC002
from pydantic import Field, computed_field

from bear_dereth.data_structs.freezing import FrozenModel
from bear_dereth.logger.common._stack_info import StackInfo  # noqa: TC001
from bear_dereth.logger.common.log_level import LogLevel


class LoggerRecord(FrozenModel):
    """A message container for queue processing."""

    msg: object = ""
    style: str = Field(default="")
    level: LogLevel = Field(default=LogLevel.DEBUG)
    stack_info: StackInfo | None = None
    timestamp: EpochTimestamp | None = None
    args: tuple[Any, ...] | None = Field(default=None, repr=False)
    kwargs: dict[str, Any] | None = Field(default=None, repr=False)

    @computed_field
    @property
    def message_str(self) -> str:
        """Message as string - handles any object type."""
        return str(self.msg)

    @computed_field
    @property
    def has_stack_info(self) -> bool:
        """Whether this record includes stack information."""
        return self.stack_info is not None

    @computed_field
    @property
    def has_timestamp(self) -> bool:
        """Whether this record includes a timestamp."""
        return self.timestamp is not None

    @classmethod
    def create(
        cls,
        msg: object,
        style: str = "",
        level: LogLevel = LogLevel.DEBUG,
        stack_info: StackInfo | None = None,
        timestamp: EpochTimestamp | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> Self:
        """Create a new LoggerRecord instance."""
        return cls(
            msg=msg,
            style=style,
            level=level,
            stack_info=stack_info,
            timestamp=timestamp,
            args=args,
            kwargs=kwargs,
        )
