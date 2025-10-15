"""Module for versioning functionality, including getting and bumping package versions."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
import re
from typing import Any, Self

from pydantic import BaseModel, Field

from bear_dereth.models.type_fields import PositiveInt  # noqa: TC001 # DO NOT REMOVE #
from bear_dereth.rich_enums import IntValue, RichIntEnum


class VersionParts(RichIntEnum):
    """Enumeration for version parts."""

    MAJOR = IntValue(value=0, text="major")
    MINOR = IntValue(value=1, text="minor")
    PATCH = IntValue(value=2, text="patch")

    @classmethod
    def choices(cls) -> list[str]:
        """Return a list of valid version parts."""
        return [part.text for part in cls]

    @classmethod
    def parts(cls) -> int:
        """Return the total number of version parts."""
        return len(cls.choices())


class Parts[*P](tuple):
    """A list subclass to represent version parts."""

    THREE_PARTS = 3
    FOUR_PARTS = 4

    @classmethod
    def split(cls, s: str, sep: str = ".") -> Parts[Any]:
        """A quick split method."""
        return Parts[int | str]([part for part in s.split(sep) if part][:4])

    @property
    def three(self) -> bool:
        """Check if the version has three parts."""
        return len(self) == self.THREE_PARTS

    @property
    def four(self) -> bool:
        """Check if the version has four parts."""
        return len(self) == self.FOUR_PARTS

    def to_three(self) -> Parts[int, int, int]:
        """Assert this is has three parts."""
        if self.three and self.is_valid:
            return Parts[int, int, int](self)
        raise ValueError("Has less or more than three parts.")

    def to_four(self) -> Parts[int, int, int, str]:
        """Assert this is has three parts."""
        if self.four and self.is_valid:
            return Parts[int, int, int, str](self)
        raise ValueError(f"Has less or more than four parts: {self}")

    def check_three_parts(self) -> bool:
        """Check that the first three parts are integers."""
        return len(self) >= self.THREE_PARTS and all(isinstance(int(part), int) for part in self[:3])

    def check_forth_part(self) -> bool:
        """Check that 4th part is a str."""
        return self.four and isinstance(str(self[3]), str)

    @property
    def is_valid(self) -> bool:
        """Check if the version parts are valid."""
        if self.three:
            return self.check_three_parts()
        if self.four:
            return self.check_three_parts() and self.check_forth_part()
        return False


class Version(BaseModel):
    """Model to represent a version string."""

    major: PositiveInt = 0
    """Major version number."""
    minor: PositiveInt = 0
    """Minor version number."""
    patch: PositiveInt = 0
    """Patch version number."""
    post: str | None = Field(default=None)
    """Post-release identifier."""

    def __repr__(self) -> str:
        """Return a string representation of the Version instance."""
        return (
            f"{self.major}.{self.minor}.{self.patch}.{self.post}"
            if self.post
            else f"{self.major}.{self.minor}.{self.patch}"
        )

    def __str__(self) -> str:
        """Return a string representation of the Version instance."""
        return self.__repr__()

    @classmethod
    def from_parts(cls, parts: Parts[Any]) -> Self:
        """Create a Version instance from individual parts."""
        if parts.three:
            int_parts: Parts[int, int, int] = parts.to_three()
            return cls(major=int_parts[0], minor=int_parts[1], patch=int_parts[2])
        if parts.four:
            full_parts: Parts[int, int, int, str] = parts.to_four()
            return cls(major=full_parts[0], minor=full_parts[1], patch=full_parts[2], post=full_parts[3])
        raise ValueError(f"Invalid number of parts. Expected 3 or 4 parts: {parts}")

    @classmethod
    def from_string(cls, version_str: str) -> Self:
        """Create a Version instance from a version string.

        Args:
            version_str: A version string in the format "major.minor.patch".

        Returns:
            A Version instance.

        Raises:
            ValueError: If the version string is not in the correct format.
        """
        if "-" in version_str:
            version_str = version_str.split("-")[0]
        if "+" in version_str:
            version_str = version_str.split("+")[0]
        version_str = re.sub(r"^[vV]", "", version_str)
        return cls.from_parts(Parts.split(version_str, "."))

    def increment(self, attr_name: str) -> None:
        """Increment the specified part of the version."""
        setattr(self, attr_name, getattr(self, attr_name) + 1)

    def default(self, part: str) -> None:
        """Clear the specified part of the version.

        Args:
            part: The part of the version to clear.
        """
        if hasattr(self, part):
            setattr(self, part, 0)

    def new_version(self, bump_type: str) -> Version:
        """Return a new version string based on the bump type."""
        bump_part: VersionParts = VersionParts.get(bump_type, default=VersionParts.PATCH)
        self.increment(bump_part.text)
        for part in VersionParts:
            if part.value > bump_part.value:
                self.default(part.text)
        return self

    @classmethod
    def from_meta(cls, package_name: str) -> Self:
        """Create a Version instance from the current package version.

        Returns:
            A Version instance with the current package version.

        Raises:
            PackageNotFoundError: If the package is not found.
        """
        try:
            return cls.from_string(version(package_name))
        except PackageNotFoundError as e:
            raise PackageNotFoundError(f"Package '{package_name}' not found: {e}") from e


__all__ = ["Parts", "Version", "VersionParts"]
