"""Bear Dereth package.

A set of common tools for various bear projects.
"""

from bear_dereth._internal.cli import main
from bear_dereth._internal.debug import METADATA

__version__: str = METADATA.version

__all__: list[str] = ["METADATA", "__version__", "main"]
