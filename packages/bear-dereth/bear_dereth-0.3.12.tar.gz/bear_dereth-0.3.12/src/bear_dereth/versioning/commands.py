"""A set of functions related to versioning."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import Any

from bear_dereth.cli import ExitCode

from .classes import Parts, Version
from .consts import VALID_BUMP_TYPES, BumpType


def bump_version(version: str, bump_type: BumpType) -> Version:
    """Bump the version based on the specified type, mutating in place since there is no reason not to.

    Args:
        version: The current version string (e.g., "1.2.3").
        bump_type: The type of bump ("major", "minor", or "patch").

    Returns:
        The new version string.

    Raises:
        ValueError: If the version format is invalid or bump_type is unsupported.
    """
    return Version.from_string(version).new_version(bump_type)


def get_version(package_name: str) -> str:
    """Get the version of the specified package.

    Args:
        package_name: The name of the package to get the version for.

    Returns:
        A Version instance representing the current version of the package.

    Raises:
        PackageNotFoundError: If the package is not found.
    """
    version: str | None = cli_get_version(package_name)
    if version is not None:
        return version
    raise ValueError("Not able to find package name.")


def cli_get_version(pkg_name: str) -> str | None:
    """Get the version of the current package.

    Returns:
        The version of the package.
    """
    try:
        current_version: str = version(pkg_name)
    except PackageNotFoundError:
        print(f"Package '{pkg_name}' not found.")
        return None
    return current_version


def cli_bump(b_type: BumpType, package_name: str, ver: str | tuple[int, int, int]) -> ExitCode:
    """Bump the version of the current package."""
    if b_type not in VALID_BUMP_TYPES:
        print(f"Invalid argument '{b_type}'. Use one of: {', '.join(VALID_BUMP_TYPES)}.")
        return ExitCode.FAILURE

    if isinstance(ver, tuple):
        try:
            parts: Parts[*tuple[Any, ...]] = Parts(ver)
            version: Version = Version.from_parts(parts)
            new_version = version.new_version(b_type)
            print(str(new_version))
            return ExitCode.SUCCESS
        except ValueError:
            new_version = Version.from_meta(package_name=package_name).new_version(b_type)
            print(str(new_version))
            return ExitCode.SUCCESS
    try:
        new_version: Version = bump_version(version=ver, bump_type=b_type)
        print(str(new_version))
        return ExitCode.SUCCESS
    except ValueError as e:
        print(f"Error: {e}")
        return ExitCode.FAILURE
    except Exception as e:
        print(f"Unexpected error: {e}")
        return ExitCode.FAILURE
