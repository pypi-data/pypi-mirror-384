"""Logger formatters for bear-dereth.

This module provides various formatter implementations for log messages,
following the Formatter protocol defined in protocols/formatter.py.
"""

from bear_dereth.logger.formatters.template_formatter import TemplateFormatter

__all__ = ["TemplateFormatter"]
