"""A set of command-line interface (CLI) utilities."""

from bear_dereth.cli.shells import DEFAULT_SHELL

from .arg_helpers import CLIArgsType, args_inject, args_parse
from .commands import GitCommand, OPShellCommand, UVShellCommand
from .exit_code import ExitCode
from .shell._base_command import BaseShellCommand
from .shell._base_shell import SimpleShellSession, shell_session

__all__ = [
    "DEFAULT_SHELL",
    "BaseShellCommand",
    "CLIArgsType",
    "ExitCode",
    "GitCommand",
    "OPShellCommand",
    "SimpleShellSession",
    "UVShellCommand",
    "args_inject",
    "args_parse",
    "shell_session",
]
