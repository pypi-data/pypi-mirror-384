from __future__ import annotations

from typing import NoReturn

from bear_dereth.data_structs.freezing import BaseHashValue, BaseNotCacheable
from bear_dereth.query._common import OpType  # noqa: TC001 # Pydantic needs access


class HashValue(BaseHashValue):
    """A simple frozen model to hold a hash value for query caching."""

    op: OpType | None

    def combine(self, other: BaseHashValue, **kwargs) -> HashValue:
        """Combine multiple hash values into one."""
        return HashValue(value=[self, other], **kwargs)

    def __hash__(self) -> int:
        if not self.cacheable:
            raise TypeError("This HashValue is not cacheable")
        return super().__hash__()


class NotCacheable(HashValue, BaseNotCacheable):
    """A singleton representing a non-cacheable hash value, contains a frozen cacheable=False flag."""

    def __init__(self) -> None: ...

    def __hash__(self) -> int:
        raise TypeError("This HashValue is not cacheable")

    def combine(self, other: BaseHashValue, **kwargs) -> NoReturn:  # noqa: ARG002
        raise TypeError("This object is not cacheable")
