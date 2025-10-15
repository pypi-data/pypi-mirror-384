"""A set of general file utility functions."""

from pathlib import Path


def touch(path: str | Path, mkdir: bool) -> Path:
    """Create a file if it doesn't exist yet and optionally create parent directories.

    This ensures a valid Path object is returned.

    Args:
        path (str | Path): Path to the file to create
        mkdir (bool): Whether to create missing parent directories
    """
    path = Path(path)
    if mkdir and not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)

    path.touch(exist_ok=True)
    return path


def get_file_hash(path: Path) -> str:
    """Get a simple SHA1 hash of a file - fast and good enough for change detection.

    Args:
        path: Path to the file to hash

    Returns:
        str: Hex digest of the file contents, or empty string if file doesn't exist
    """
    from hashlib import sha1  # noqa: PLC0415

    try:
        return sha1(path.read_bytes(), usedforsecurity=False).hexdigest()
    except Exception:
        return ""  # File read error, treat as "no file"


def has_file_changed(path: Path, last_known_hash: str) -> tuple[bool, str]:
    """Function version - check if file changed and return new hash.

    Args:
        path: Path to check
        last_known_hash: Previous hash to compare against

    Returns:
        tuple[bool, str]: (has_changed, current_hash)
    """
    current_hash: str = get_file_hash(path)
    return (current_hash != last_known_hash, current_hash)


class FileWatcher:
    """Simple file change detection using SHA1 hashing."""

    def __init__(self, filepath: str | Path) -> None:
        """Initialize FileWatcher.

        Args:
            filepath: Path to the file to watch
        """
        self.path = Path(filepath)
        self._last_hash: str = get_file_hash(self.path)

    @property
    def changed(self) -> bool:
        """Check if file has changed since last check."""
        return self.has_changed()

    def has_changed(self) -> bool:
        """Check if file has changed since last check.

        Returns:
            bool: True if file changed, False otherwise
        """
        current_hash: str = get_file_hash(self.path)
        if current_hash != self._last_hash:
            self._last_hash = current_hash
            return True
        return False

    @property
    def current_hash(self) -> str:
        """Get current file hash without updating internal state."""
        return get_file_hash(self.path)


def derive_settings_path(
    name: str,
    file_name: str | None,
    path: Path | str | None = None,
    ext: str = "json",
) -> Path:
    """Get the path to the settings file based on app name, optional file name, and optional path.

    Args:
        name: App name (used as default file name and for default directory)
        file_name: Optional specific file name (overrides name for filename)
        path: Optional path - can be:
            - Full path to .json file (returns as-is)
            - Directory path (file will be created inside)
            - None (uses default settings directory)
        ext: File extension (default: "json")

    Returns:
        Path: Full path to the settings JSON file

    Examples:
        get_path("myapp")
        # -> ~/.config/myapp/settings/myapp.json

        get_path("myapp", "custom")
        # -> ~/.config/myapp/settings/custom.json

        get_path("myapp", None, "/tmp")
        # -> /tmp/myapp.json

        get_path("myapp", "custom", "/tmp")
        # -> /tmp/custom.json

        get_path("myapp", None, "/full/path/config.json")
        # -> /full/path/config.json
    """
    from bear_dereth.config.dir_manager import get_settings_path  # noqa: PLC0415

    if ext in {"memory", "default"}:
        ext = "json"
    ext = f".{ext}"
    if path is not None and str(path).endswith(ext):
        path_obj: Path = Path(path).resolve()
        if path_obj.is_absolute() or "/" in str(path):
            return path_obj
    filename_base: str = name if file_name is None else Path(file_name).stem
    root_path: Path = Path(path) if path is not None else get_settings_path(name, mkdir=True)
    return root_path / f"{filename_base}{ext}"
