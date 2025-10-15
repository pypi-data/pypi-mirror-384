from collections.abc import Callable
from io import StringIO
from typing import IO, Literal, TextIO, overload

from bear_dereth.files.textio_utility import stderr
from bear_dereth.logger.common.consts import FILE_MODE, BaseOutput, CallableOrFile


@overload
def file_mode_get(mode: Literal["stdout"]) -> Callable[[], TextIO]: ...
@overload
def file_mode_get(mode: Literal["stderr"]) -> Callable[[], TextIO]: ...
@overload
def file_mode_get(mode: Literal["devnull"]) -> Callable[[], IO[str]]: ...
@overload
def file_mode_get(mode: Literal["string_io"]) -> Callable[[], StringIO]: ...


def file_mode_get(mode: BaseOutput) -> Callable[[], TextIO | IO[str] | StringIO]:
    """Get the file mode callable based on the provided mode string.

    Args:
        mode: A string representing the desired file mode.

    Returns:
        A callable that returns a TextIO or IO object corresponding to the mode.
    """
    return FILE_MODE.get(mode, stderr)


def get_file_mode(
    mode: BaseOutput | None = None,
    callback: CallableOrFile | None = None,
    file: CallableOrFile | None = None,
) -> CallableOrFile:
    """Based upon what is passed in, return the appropriate file mode callable.

    Args:
        mode: A string representing the desired file mode.
        file_callback: A callable that returns a TextIO or IO object.
        file: A specific TextIO or IO object to use.

    Returns:
        A callable that returns a TextIO or IO object corresponding to the mode.
    """
    if file is None and callback is None and mode is not None:
        return file_mode_get(mode)
    return file if file is not None else callback if callback is not None else stderr
