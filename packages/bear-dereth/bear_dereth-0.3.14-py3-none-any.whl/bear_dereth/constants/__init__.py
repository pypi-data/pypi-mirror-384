"""A set of helpful constants used throughout the Bear Dereth and beyond!"""

from pathlib import Path

from bear_dereth.cli.exit_code import ExitCode

from .http_status_code import HTTPStatusCode


def get_config_path() -> Path:
    """Get the path to the configuration directory based on the operating system."""
    from os import environ  # noqa: PLC0415

    if "XDG_CONFIG_HOME" in environ:
        return Path(environ["XDG_CONFIG_HOME"])
    if "APPDATA" in environ:
        return Path(environ["APPDATA"])
    return Path.home() / ".config"


PATH_TO_DOWNLOADS: Path = Path.home() / "Downloads"
"""Path to the Downloads folder."""
PATH_TO_PICTURES: Path = Path.home() / "Pictures"
"""Path to the Pictures folder."""
PATH_TO_DOCUMENTS: Path = Path.home() / "Documents"
"""Path to the Documents folder."""
PATH_TO_HOME: Path = Path.home()
"""Path to the user's home directory."""
PATH_TO_CONFIG: Path = get_config_path()
"""Path to the configuration directory based on the operating system."""


VIDEO_EXTS: list[str] = [".mp4", ".mov", ".avi", ".mkv"]
"""Extensions for video files."""
IMAGE_EXTS: list[str] = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
"""Extensions for image files."""
FILE_EXTS: list[str] = IMAGE_EXTS + VIDEO_EXTS
"""Extensions for both image and video files."""

__all__ = [
    "FILE_EXTS",
    "IMAGE_EXTS",
    "PATH_TO_CONFIG",
    "PATH_TO_DOCUMENTS",
    "PATH_TO_DOWNLOADS",
    "PATH_TO_HOME",
    "PATH_TO_PICTURES",
    "VIDEO_EXTS",
    "ExitCode",
    "HTTPStatusCode",
]
