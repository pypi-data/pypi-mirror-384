"""fastalloc - high-performance python memory pool library."""

from .__version__ import __version__
from .async_support import AsyncPool
from .config import GrowthConfig, GrowthStrategy, InitializationStrategy, PoolBuilder
from .decorators import pooled
from .exceptions import (
    AlreadyReleasedError,
    FastAllocError,
    InvalidCapacityError,
    PoolClosedError,
    PoolConfigurationError,
    PoolEmptyError,
    TypeMismatchError,
)
from .pool import FixedPool, GrowingPool, ThreadLocalPool, ThreadSafePool
from .protocols import Resettable
from .stats import StatsCollector, StatsReporter

# main pool interface - defaults to fixed pool but is a union type
Pool = FixedPool

__all__ = [
    # version
    "__version__",
    # main pool types
    "Pool",
    "FixedPool",
    "GrowingPool",
    "ThreadSafePool",
    "ThreadLocalPool",
    "AsyncPool",
    # builder
    "PoolBuilder",
    # configuration
    "GrowthStrategy",
    "GrowthConfig",
    "InitializationStrategy",
    # decorators
    "pooled",
    # exceptions
    "FastAllocError",
    "PoolEmptyError",
    "PoolClosedError",
    "TypeMismatchError",
    "InvalidCapacityError",
    "AlreadyReleasedError",
    "PoolConfigurationError",
    # statistics
    "StatsCollector",
    "StatsReporter",
    # protocols
    "Resettable",
]
