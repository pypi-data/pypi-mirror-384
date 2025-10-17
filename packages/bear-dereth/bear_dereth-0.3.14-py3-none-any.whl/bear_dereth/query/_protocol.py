"""A protocol for query-like objects."""

from __future__ import annotations

from typing import Protocol


class QueryProtocol[T](Protocol):
    """A protocol for query-like objects."""

    def __call__(self, value: T) -> bool: ...
    @property
    def is_cacheable(self) -> bool: ...
    def __hash__(self) -> int: ...


__all__ = ["QueryProtocol"]
