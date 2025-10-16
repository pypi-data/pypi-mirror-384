"""async pool implementation."""

import asyncio
from typing import Callable, Optional, Set, Type, TypeVar

from ..allocator.stack import StackAllocator
from ..config.initialization import InitializationStrategy
from ..exceptions import PoolClosedError, PoolEmptyError
from ..pool.base import BasePool
from ..stats.collector import now_ns
from .handle import AsyncContextHandle

T = TypeVar("T")


class AsyncPool(BasePool[T]):
    # purpose: a pool designed for async/await code with async locks.
    # params: same as BasePool.
    # args: obj_type and capacity required, rest optional.
    # returns: n/a - initializer.
    # raises: PoolConfigurationError for invalid settings.
    """async-compatible pool using asyncio locks."""

    # purpose: creates an async pool with async locking.
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

        # async lock for concurrency control
        self._lock = asyncio.Lock()

        # allocator and tracking
        self._allocator: StackAllocator[T] = StackAllocator()
        self._in_use: Set[int] = set()

        # pre-initialize if requested (synchronously during init)
        if self._initialization_strategy == InitializationStrategy.EAGER:
            self._preallocate()

    # purpose: creates all objects up front.
    # params: self.
    # args: none.
    # returns: nothing.
    # raises: whatever factory raises.
    def _preallocate(self) -> None:
        """pre-allocate all objects."""
        for _ in range(self._capacity):
            obj = self._create_object()
            self._allocator.push(obj)

    # purpose: gets an object from pool in async-safe way.
    # params: self.
    # args: none.
    # returns: object from pool (regular, not awaitable).
    # raises: PoolEmptyError, PoolClosedError.
    def get(self) -> T:
        """acquire an object from the pool (use with await get_async for async)."""
        # note: this is sync version for compatibility
        # users should prefer get_async in async code
        if self._closed:
            raise PoolClosedError("pool is closed")

        start_time = now_ns() if self._stats.enabled else 0

        # try to get from free list
        obj = self._allocator.pop()

        if obj is None:
            # lazy initialization
            if len(self._in_use) < self._capacity:
                obj = self._create_object()
            else:
                raise PoolEmptyError("pool is empty")

        # reset object
        self._reset_object(obj)

        # track in use
        obj_id = id(obj)
        self._in_use.add(obj_id)

        # stats (always record for size() tracking, duration only if enabled)
        duration = now_ns() - start_time if self._stats.enabled else 0
        self._stats.record_allocation(duration)

        return obj

    # purpose: gets an object from pool with async locking (awaitable version).
    # params: self.
    # args: none.
    # returns: awaitable that gives object from pool.
    # raises: PoolEmptyError, PoolClosedError.
    async def get_async(self) -> T:
        """acquire an object from the pool (async version)."""
        if self._closed:
            raise PoolClosedError("pool is closed")

        start_time = now_ns() if self._stats.enabled else 0

        async with self._lock:
            # try to get from free list
            obj = self._allocator.pop()

            if obj is None:
                # lazy initialization
                if len(self._in_use) < self._capacity:
                    obj = self._create_object()
                else:
                    raise PoolEmptyError("pool is empty")

            # reset object
            self._reset_object(obj)

            # track in use
            obj_id = id(obj)
            self._in_use.add(obj_id)

            # stats (always record for size() tracking, duration only if enabled)
            duration = now_ns() - start_time if self._stats.enabled else 0
            self._stats.record_allocation(duration)

        return obj

    # purpose: returns object back to pool.
    # params: self, obj - object to return.
    # args: obj required.
    # returns: nothing.
    # raises: TypeMismatchError, AlreadyReleasedError.
    def release(self, obj: T) -> None:
        """release an object back to the pool."""
        self._validate_object(obj)

        start_time = now_ns() if self._stats.enabled else 0

        obj_id = id(obj)

        # check if already released
        if obj_id not in self._in_use:
            from ..exceptions import AlreadyReleasedError

            raise AlreadyReleasedError("object was already released or not from this pool")

        # remove from in-use tracking
        self._in_use.remove(obj_id)

        # return to free list
        self._allocator.push(obj)

        # stats (always record for size() tracking, duration only if enabled)
        duration = now_ns() - start_time if self._stats.enabled else 0
        self._stats.record_release(duration)

    # purpose: returns object with async locking (awaitable version).
    # params: self, obj - object to return.
    # args: obj required.
    # returns: awaitable that completes when released.
    # raises: TypeMismatchError, AlreadyReleasedError.
    async def release_async(self, obj: T) -> None:
        """release an object back to the pool (async version)."""
        self._validate_object(obj)

        start_time = now_ns() if self._stats.enabled else 0

        async with self._lock:
            obj_id = id(obj)

            # check if already released
            if obj_id not in self._in_use:
                from ..exceptions import AlreadyReleasedError

                raise AlreadyReleasedError("object was already released or not from this pool")

            # remove from in-use tracking
            self._in_use.remove(obj_id)

            # return to free list
            self._allocator.push(obj)

            # stats (always record for size() tracking, duration only if enabled)
            duration = now_ns() - start_time if self._stats.enabled else 0
            self._stats.record_release(duration)

    # purpose: gets object with async context manager for auto-release.
    # params: self.
    # args: none.
    # returns: AsyncContextHandle that auto-releases.
    # raises: PoolEmptyError, PoolClosedError.
    def allocate(self) -> AsyncContextHandle[T]:
        """allocate an object with async context manager."""
        obj = self.get()
        return AsyncContextHandle(obj, self.release)

    # purpose: tells how many objects are available.
    # params: self.
    # args: none.
    # returns: count of available objects.
    # raises: none.
    def available(self) -> int:
        """return number of available objects."""
        return self._allocator.size()
