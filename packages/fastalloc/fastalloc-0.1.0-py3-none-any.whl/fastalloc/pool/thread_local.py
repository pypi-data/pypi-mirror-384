"""thread-local pool implementation."""

import threading
from typing import Callable, Dict, Optional, Type, TypeVar

from ..config.initialization import InitializationStrategy
from ..stats.collector import StatsCollector
from .base import BasePool
from .fixed import FixedPool

T = TypeVar("T")


class ThreadLocalPool(BasePool[T]):
    # purpose: gives each thread its own separate pool so no locking needed.
    # params: same as BasePool.
    # args: obj_type and capacity required, rest optional.
    # returns: n/a - initializer.
    # raises: PoolConfigurationError for invalid settings.
    """thread-local pool with per-thread instances."""

    # purpose: creates a thread-local pool manager.
    # params: same as BasePool.
    # args: obj_type and capacity required, rest keyword-only.
    # returns: n/a - initializer.
    # raises: PoolConfigurationError for invalid config.
    def __init__(
        self,
        obj_type: Type[T],
        capacity: int,
        *,
        factory: Optional[Callable[[], T]] = None,
        reset_method: Optional[str] = None,
        enable_statistics: bool = False,
        pre_initialize: bool = False,
    ) -> None:
        super().__init__(
            obj_type,
            capacity,
            factory=factory,
            reset_method=reset_method,
            enable_statistics=enable_statistics,
            pre_initialize=pre_initialize,
        )

        # thread-local storage for per-thread pools
        self._local = threading.local()

        # track all thread pools for aggregation
        self._thread_pools: Dict[int, FixedPool[T]] = {}
        self._thread_pools_lock = threading.Lock()

    # purpose: gets or creates the pool for the current thread.
    # params: self.
    # args: none.
    # returns: the pool for this thread.
    # raises: none.
    def _get_thread_pool(self) -> FixedPool[T]:
        """get or create pool for current thread."""
        if not hasattr(self._local, "pool"):
            # create new pool for this thread
            pool = FixedPool(
                self._obj_type,
                self._capacity,
                factory=self._factory,
                reset_method=self._reset_method,
                enable_statistics=self._stats.enabled,
                pre_initialize=(
                    self._initialization_strategy == InitializationStrategy.EAGER
                ),
            )
            self._local.pool = pool

            # track for aggregation
            thread_id = threading.get_ident()
            with self._thread_pools_lock:
                self._thread_pools[thread_id] = pool

        return self._local.pool

    # purpose: gets an object from the current thread's pool.
    # params: self.
    # args: none.
    # returns: object from pool.
    # raises: PoolEmptyError, PoolClosedError.
    def get(self) -> T:
        """acquire an object from thread-local pool."""
        self._check_closed()
        pool = self._get_thread_pool()
        return pool.get()

    # purpose: returns object to current thread's pool.
    # params: self, obj - object to return.
    # args: obj required.
    # returns: nothing.
    # raises: TypeMismatchError, AlreadyReleasedError.
    def release(self, obj: T) -> None:
        """release an object back to thread-local pool."""
        pool = self._get_thread_pool()
        pool.release(obj)

    # purpose: tells how many objects are available in current thread's pool.
    # params: self.
    # args: none.
    # returns: count of available objects.
    # raises: none.
    def available(self) -> int:
        """return number of available objects in thread-local pool."""
        pool = self._get_thread_pool()
        return pool.available()

    # purpose: gets aggregated statistics from all thread pools.
    # params: self.
    # args: none.
    # returns: StatsCollector with combined stats.
    # raises: none.
    def stats(self) -> StatsCollector:
        """get aggregated statistics from all thread pools."""
        aggregated = StatsCollector(enabled=self._stats.enabled)

        with self._thread_pools_lock:
            for pool in self._thread_pools.values():
                aggregated.merge(pool.stats())

        return aggregated

    # purpose: closes all thread pools.
    # params: self.
    # args: none.
    # returns: nothing.
    # raises: none.
    def close(self) -> None:
        """close all thread pools."""
        super().close()

        with self._thread_pools_lock:
            for pool in self._thread_pools.values():
                pool.close()
