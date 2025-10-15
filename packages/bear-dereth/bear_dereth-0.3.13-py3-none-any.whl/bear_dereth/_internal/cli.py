from __future__ import annotations

from argparse import ArgumentParser, Namespace
import sys

from bear_dereth._internal._info import METADATA
from bear_dereth._internal.debug import _print_debug_info  # type: ignore[import]
from bear_dereth.cli import CLIArgsType, ExitCode, args_inject
from bear_dereth.versioning.commands import cli_bump
from bear_dereth.versioning.consts import VALID_BUMP_TYPES, BumpType


def _debug_info(no_color: bool = False) -> ExitCode:
    """CLI command to print debug information."""
    _print_debug_info(no_color=no_color)
    return ExitCode.SUCCESS


def _version(name: bool = False) -> ExitCode:
    """CLI command to get the current version of the package."""
    to_print: str = ""
    if name:
        to_print += METADATA.name + " "
    to_print += METADATA.version
    print(to_print)
    return ExitCode.SUCCESS


def _bump(bump_type: BumpType) -> ExitCode:
    """CLI command to bump the version of the package."""
    return cli_bump(b_type=bump_type, package_name=METADATA.name, ver=METADATA.version_tuple)


def _get_args(args: CLIArgsType) -> Namespace:
    name: str = METADATA.name
    parser = ArgumentParser(description=name.capitalize(), prog=name, exit_on_error=False)
    subparser = parser.add_subparsers(dest="command", required=False, help="Available commands")
    subparser.add_parser("version", help="Get the current version of the package")
    debug = subparser.add_parser("debug_info", help="Print debug information")
    debug.add_argument("-n", "--no-color", action="store_true", help="Disable color output")
    bump: ArgumentParser = subparser.add_parser("bump")
    bump.add_argument("bump_type", type=str, choices=VALID_BUMP_TYPES, help="major, minor, or patch")
    return parser.parse_args(args)


@args_inject(process=_get_args)
def main(args: Namespace) -> ExitCode:
    """Entry point for the CLI application.

    This function is executed when you type `bear_dereth` or `python -m bear_dereth`.

    Parameters:
        args: Arguments passed from the command line.

    Returns:
        An exit code.
    """
    try:
        if args.command == "version":
            return _version()
        if args.command == "debug_info":
            return _debug_info()
        if args.command == "bump":
            return _bump(bump_type=args.bump_type)
        return ExitCode.SUCCESS
    except SystemExit as e:
        if e.code is not None and isinstance(e.code, int):
            return ExitCode(e.code)
        return ExitCode.SUCCESS
    except Exception:
        return ExitCode.FAILURE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
