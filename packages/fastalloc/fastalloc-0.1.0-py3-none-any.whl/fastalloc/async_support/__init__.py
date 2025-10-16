"""async support for fastalloc."""

from .handle import AsyncContextHandle
from .pool import AsyncPool

__all__ = [
    "AsyncPool",
    "AsyncContextHandle",
]
