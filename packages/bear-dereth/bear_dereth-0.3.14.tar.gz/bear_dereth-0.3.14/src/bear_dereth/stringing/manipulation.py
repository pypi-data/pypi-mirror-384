"""A utility to create slugs from strings."""

from functools import cached_property
import re
from typing import Literal
import unicodedata

from bear_dereth.lazy_imports import lazy

json = lazy("json")


def join_dicts(data: list[dict], sep: str = "\n") -> str:
    """Join a list of dictionaries into a single string with each dictionary serialized as JSON.

    Might use this with JSONL files.

    Args:
        data (list[dict]): List of dictionaries to join.
        sep (str): Separator to use between items. Defaults to newline.

    Returns:
        str: The joined string.
    """
    return sep.join(ln if isinstance(ln, str) else json.dumps(ln, ensure_ascii=False) for ln in data)


def slugify(value: str, sep: str = "-") -> str:
    """Return an ASCII slug for ``value``.

    Args:
        value: String to normalize.
        sep: Character used to replace whitespace and punctuation.

    Returns:
        A sluggified version of ``value``.
    """
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-_\s]+", sep, value).strip("-_")


CaseChoices = Literal["snake", "kebab", "camel", "pascal", "screaming_snake"]


class CaseConverter:
    """String casing utilities."""

    @cached_property
    def _cts_pattern(self) -> re.Pattern[str]:
        """Regex pattern to convert camelCase to snake_case.

        Returns:
            Compiled regex pattern for camelCase to snake_case conversion.
        """
        return re.compile(
            r"""
                (?<=[a-z])      # preceded by lowercase
                (?=[A-Z])       # followed by uppercase
                |               # OR
                (?<=[A-Z])      # preceded by lowercase
                (?=[A-Z][a-z])  # followed by uppercase, then lowercase
            """,
            re.X,
        )

    def camel_to_snake(self, value: str) -> str:
        """Convert a camelCase string to snake_case.

        Args:
            value: The camelCase string to convert.

        Returns:
            The converted snake_case string.
        """
        return self._cts_pattern.sub("_", value).lower()

    def snake_to_pascal(self, value: str) -> str:
        """Convert a snake_case string to PascalCase.

        Args:
            value: The snake_case string to convert.

        Returns:
            The converted PascalCase string.
        """
        return "".join(word.capitalize() for word in value.split("_"))

    def camel_to_pascal(self, value: str) -> str:
        """Convert a camelCase string to PascalCase.

        Args:
            value: The camelCase string to convert.

        Returns:
            The converted PascalCase string.
        """
        return value[0].upper() + value[1:] if value else ""

    def snake_to_kebab(self, value: str) -> str:
        """Convert a snake_case string to kebab-case.

        Args:
            value: The snake_case string to convert.

        Returns:
            The converted kebab-case string.
        """
        return value.replace("_", "-")

    def detect_case(self, value: str) -> str:
        """Detect the casing format of a string.

        Args:
            value: The string to analyze.

        Returns:
            The detected case format: 'snake', 'kebab', 'camel', 'pascal', 'screaming_snake', or 'unknown'.
        """
        if not value:
            return "unknown"
        has_underscores: bool = "_" in value
        has_dashes: bool = "-" in value
        has_uppercase: bool = any(c.isupper() for c in value)
        has_lowercase: bool = any(c.islower() for c in value)
        starts_with_upper: bool = value[0].isupper()
        has_spaces: bool = " " in value
        if has_spaces:
            return "unknown"
        if has_underscores and has_uppercase and not has_lowercase:
            return "screaming_snake"
        if has_underscores and not has_uppercase:
            return "snake"
        if has_dashes and not has_uppercase:
            return "kebab"
        if starts_with_upper and has_uppercase and has_lowercase and not has_underscores and not has_dashes:
            return "pascal"
        if not starts_with_upper and has_uppercase and has_lowercase and not has_underscores and not has_dashes:
            return "camel"
        return "unknown"

    def _normalized_case(self, value: str) -> str:
        current_case: str = self.detect_case(value)
        if current_case in {"camel", "pascal"}:
            return self.camel_to_snake(value)
        if current_case == "kebab":
            return value.replace("-", "_")
        if current_case == "screaming_snake":
            return value.lower()
        if current_case == "snake":
            return value
        return value

    def convert_to(self, value: str, target_case: CaseChoices) -> str:
        """Convert a string to the target case format, auto-detecting the source format.

        Args:
            value: The string to convert.
            target_case: The target case format ('snake', 'kebab', 'camel', 'pascal').

        Returns:
            The converted string.

        Raises:
            ValueError: If the target case is not supported.
        """
        normalized: str = self._normalized_case(value)
        match target_case:
            case "snake":
                return normalized
            case "kebab":
                return normalized.replace("_", "-")
            case "camel":
                words: list[str] = normalized.split("_")
                return words[0] + "".join(word.capitalize() for word in words[1:])
            case "pascal":
                return self.snake_to_pascal(normalized)
            case "screaming_snake":
                return normalized.upper()
            case _:
                raise ValueError(f"Unsupported target case: {target_case}")


def to_snake(value: str) -> str:
    """Convert a string to snake_case.

    Args:
        value: The string to convert.

    Returns:
        The converted snake_case string.
    """
    return CaseConverter().convert_to(value, "snake")


def to_kebab(value: str) -> str:
    """Convert a string to kebab-case.

    Args:
        value: The string to convert.

    Returns:
        The converted kebab-case string.
    """
    return CaseConverter().convert_to(value, "kebab")


def to_camel(value: str) -> str:
    """Convert a string to camelCase.

    Args:
        value: The string to convert.

    Returns:
        The converted camelCase string.
    """
    return CaseConverter().convert_to(value, "camel")


def to_pascal(value: str) -> str:
    """Convert a string to PascalCase.

    Args:
        value: The string to convert.

    Returns:
        The converted PascalCase string.
    """
    return CaseConverter().convert_to(value, "pascal")


def to_screaming_snake(value: str) -> str:
    """Convert a string to SCREAMING_SNAKE_CASE.

    Args:
        value: The string to convert.

    Returns:
        The converted SCREAMING_SNAKE_CASE string.
    """
    return CaseConverter().convert_to(value, "screaming_snake")


def detect_case(value: str) -> str:
    """Detect the casing format of a string.

    Args:
        value: The string to analyze.

    Returns:
        The detected case format: 'snake', 'kebab', 'camel', 'pascal', 'screaming_snake', or 'unknown'.
    """
    return CaseConverter().detect_case(value)


def convert_case(value: str, target_case: CaseChoices) -> str:
    """Convert a string to the target case format, auto-detecting the source format.

    Args:
        value: The string to convert.
        target_case: The target case format ('snake', 'kebab', 'camel', 'pascal', 'screaming_snake').

    Returns:
        The converted string.
    """
    return CaseConverter().convert_to(value, target_case)


def truncate(
    value: str,
    max_length: int,
    suffix: str = "...",
    word_boundary: bool = False,
) -> str:
    """Truncate string to max_length, adding suffix if truncated.

    Args:
        value: String to truncate.
        max_length: Maximum length including suffix.
        suffix: String to append when truncated (default "...").
        word_boundary: If True, truncate at word boundary to avoid cutting words,
            raises a silly error if no spaces are found.

    Returns:
        Truncated string with suffix, or original string if no truncation needed.

    Examples:
        >>> truncate("Hello world", 8)
        'Hello...'
        >>> truncate("Hello world", 8, word_boundary=True)
        'Hello...'
    """
    if len(value) <= max_length:
        return value
    truncate_at: int = max_length - len(suffix)
    if truncate_at <= 0:
        return suffix[:max_length]
    if word_boundary and " " not in value:
        raise ValueError("WHERE ARE YOUR SPACES????????????? :O")
    if word_boundary:
        truncated: str = value[:truncate_at]
        last_space: int = truncated.rfind(" ")
        if last_space > 0:
            truncated = truncated[:last_space]
        return f"{truncated}{suffix}"
    return f"{value[:truncate_at]}{suffix}"


__all__ = [
    "CaseConverter",
    "convert_case",
    "detect_case",
    "slugify",
    "to_camel",
    "to_kebab",
    "to_pascal",
    "to_screaming_snake",
    "to_snake",
]

if __name__ == "__main__":
    # Example usage
    original = "ExampleStringForConversionWithVariousThings"
    print("Original:", original)
    print("Slugified:", slugify(original))
    print("To Snake:", to_snake(original))
    print("To Kebab:", to_kebab(original))
    print("To Camel:", to_camel(original))
    print("To Pascal:", to_pascal(original))
    print("To Screaming Snake:", to_screaming_snake(original))
    print("Detected Case:", detect_case(original))
    print("Truncated:", truncate(original, 30))
