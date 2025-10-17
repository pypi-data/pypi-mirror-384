"""A coverage checking tool using pytest and pytest-cov."""

from argparse import ArgumentParser, Namespace
from pathlib import Path
import sys
from typing import TYPE_CHECKING

from bear_dereth._internal._info import METADATA
from bear_dereth.cli import ExitCode, args_inject
from bear_dereth.cli.commands import BaseShellCommand

if TYPE_CHECKING:
    from subprocess import CompletedProcess


class PytestCmd(BaseShellCommand):
    command_name = str(Path(sys.executable).parent / "pytest")


def get_args(args: list[str]) -> Namespace:
    parser = ArgumentParser(prog="test_coverage_check")
    parser.add_argument(
        "-m",
        "--module",
        action="store",
        type=str,
        default="tests",
        help="The test module to run (default: tests)",
    )
    parser.add_argument(
        "-c",
        "--cov",
        action="store",
        type=str,
        default=METADATA.project_name,
        help="The module to check coverage for (default: bear_dereth)",
    )
    parser.add_argument(
        "--cov-fail-under",
        action="store",
        type=int,
        default=100,
        help="The minimum coverage percentage required (default: 100)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Increase output verbosity",
    )
    parser.add_argument(
        "--cov-report",
        action="store",
        type=str,
        default="term",
        help="Type of coverage report to generate (default: term)",
    )
    parser.add_argument(
        "--show-missing",
        action="store_true",
        help="Show line numbers of statements that weren't executed",
    )
    parser.add_argument(
        "--cov-branch",
        action="store_true",
        help="Measure branch coverage in addition to statement coverage",
    )
    parser.add_argument(
        "--junitxml",
        action="store",
        type=str,
        default=None,
        help="Path to save JUnit XML test results (e.g., reports/junit/test-results.xml)",
    )
    parser.add_argument(
        "--html",
        action="store",
        type=str,
        default=None,
        help="Path to save HTML coverage report (e.g., reports/html)",
    )
    return parser.parse_args(args)


def build_pytest_cmd(args: Namespace) -> str:
    if not args.module:
        args.module = "tests"
    if not args.cov:
        args.cov = METADATA.project_name
    pytest_args: list[str] = [
        args.module,
        f"--cov={args.cov}",
        f"--cov-fail-under={args.cov_fail_under}",
    ]
    # Only show detailed report if --show-missing is passed
    if args.show_missing:
        pytest_args.append(f"--cov-report={args.cov_report}:skip-covered")
    else:
        # Just show summary, no per-file details
        pytest_args.append("--cov-report=term:skip-covered")
        pytest_args.append("--no-cov-on-fail")
        # Add quiet flag to minimize output
        pytest_args.append("-q")
    if args.junitxml:
        pytest_args.append(f"--junitxml={args.junitxml}")
    if args.html:
        pytest_args.append(f"--cov-report=html:{args.html}")
    if args.cov_branch:
        pytest_args.append("--cov-branch")
    if args.verbose:
        pytest_args.append("-v")
    return " ".join(pytest_args)


@args_inject(process=get_args)
def main(args: Namespace) -> ExitCode:
    """Run pytest with coverage checking."""
    try:
        pytest_cmd = PytestCmd(build_pytest_cmd(args))
        result: CompletedProcess[str] = pytest_cmd.do().get_result()
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        if result.returncode != 0:
            return ExitCode.FAILURE
        return ExitCode.SUCCESS
    except Exception as e:
        print(f"Error running tests: {e}", file=sys.stderr)
        return ExitCode.FAILURE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
