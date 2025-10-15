"""BasePrinter protocol definition."""

from __future__ import annotations

import inspect
from pathlib import Path
import sys
from sys import exc_info
from types import FrameType  # noqa: TC003
from typing import TYPE_CHECKING

from pydantic import BaseModel, computed_field

if TYPE_CHECKING:
    from collections.abc import Callable


class StackInfo(BaseModel):
    """A model to hold stack information."""

    model_config = {"arbitrary_types_allowed": True}

    caller_function: str
    filename: Path
    line_number: int
    code_context: list[str] | None
    index: int | None
    stack_value: int | None = None
    exec_frame: FrameType | None = None

    @computed_field
    @property
    def filename_short(self) -> str:
        """Just the filename without path - perfect for log formatting."""
        return self.filename.name

    @computed_field
    @property
    def filepath_str(self) -> str:
        """Full file path as string - useful for detailed logging."""
        return str(self.filename)

    @computed_field
    @property
    def code_line(self) -> str:
        """The actual code line if available, otherwise '<unknown>'."""
        if self.code_context and self.index is not None:
            return self.code_context[self.index].strip()
        return "<unknown>"

    @computed_field
    @property
    def location(self) -> str:
        """Formatted location string: filename:line_number."""
        return f"{self.filename.name}:{self.line_number}"

    @computed_field
    @property
    def full_location(self) -> str:
        """Formatted location with function: filename:line_number@function."""
        return f"{self.filename.name}:{self.line_number}@{self.caller_function}"

    @classmethod
    def from_current_stack(cls, ignored_functions: set[str] | None = None) -> StackInfo:
        """Create a StackInfo instance from the current stack, ignoring specified functions."""
        ignored = {
            "_wrapped_print",
            "on_error_callback",
            "emit",
            "_emit_to_handlers",
            "from_current_stack",
        }
        if ignored_functions is not None:
            ignored: set[str] = ignored.union(ignored_functions)

        exec_frame: FrameType | None = get_frame_fallback(2)
        stack: list[inspect.FrameInfo] = inspect.stack()
        stack_value = 0
        while stack_value < len(stack) and stack[stack_value].function in ignored:
            stack_value += 1

        caller_frame: inspect.FrameInfo = stack[stack_value]
        return cls(
            caller_function=caller_frame.function,
            filename=Path(caller_frame.filename).resolve(),
            line_number=caller_frame.lineno,
            code_context=caller_frame.code_context,
            index=caller_frame.index,
            stack_value=stack_value,
            exec_frame=exec_frame,
        )


def get_frame_fallback(n: int) -> FrameType | None:
    try:
        raise Exception  # noqa: TRY301 TRY002
    except Exception:
        frame = exc_info()[2]
        if frame is not None:
            frame = frame.tb_frame.f_back
        for _ in range(n):
            if frame is not None:
                frame = frame.f_back
        return frame


def load_get_frame_function() -> Callable[[int], FrameType] | Callable[..., FrameType | None]:
    if hasattr(sys, "_getframe"):  # noqa: SIM108
        get_frame = sys._getframe  # type: ignore[attr-defined]
    else:
        get_frame = get_frame_fallback
    return get_frame


get_frame: Callable[[int], FrameType] | Callable[..., FrameType | None] = load_get_frame_function()
