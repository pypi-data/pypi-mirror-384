"""thread-safe pool implementation."""

from threading import Lock
from typing import Callable, Optional, Set, Type, TypeVar

from ..allocator.stack import StackAllocator
from ..config.initialization import InitializationStrategy
from ..exceptions import PoolEmptyError
from ..stats.collector import now_ns
from .base import BasePool

T = TypeVar("T")


class ThreadSafePool(BasePool[T]):
    # purpose: a pool that multiple threads can use safely at the same time.
    # params: same as BasePool plus thread safety.
    # args: obj_type and capacity required, rest optional.
    # returns: n/a - initializer.
    # raises: PoolConfigurationError for invalid settings.
    """thread-safe pool using locks."""

    # purpose: creates a pool with locking for thread safety.
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

        # lock for thread safety
        self._lock = Lock()

        # allocator and tracking
        self._allocator: StackAllocator[T] = StackAllocator()
        self._in_use: Set[int] = set()

        # pre-initialize if requested
        if self._initialization_strategy == InitializationStrategy.EAGER:
            self._preallocate()

    # purpose: creates all objects up front.
    # params: self.
    # args: none.
    # returns: nothing.
    # raises: whatever factory raises.
    def _preallocate(self) -> None:
        """pre-allocate all objects."""
        with self._lock:
            for _ in range(self._capacity):
                obj = self._create_object()
                self._allocator.push(obj)

    # purpose: gets an object from pool in a thread-safe way.
    # params: self.
    # args: none.
    # returns: object from pool.
    # raises: PoolEmptyError if none available, PoolClosedError if closed.
    def get(self) -> T:
        """acquire an object from the pool (thread-safe)."""
        self._check_closed()

        start_time = now_ns() if self._stats.enabled else 0

        with self._lock:
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

    # purpose: returns object to pool in thread-safe way.
    # params: self, obj - object to return.
    # args: obj required.
    # returns: nothing.
    # raises: TypeMismatchError, AlreadyReleasedError.
    def release(self, obj: T) -> None:
        """release an object back to the pool (thread-safe)."""
        self._validate_object(obj)

        start_time = now_ns() if self._stats.enabled else 0

        with self._lock:
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

    # purpose: tells how many free objects available.
    # params: self.
    # args: none.
    # returns: count of available objects.
    # raises: none.
    def available(self) -> int:
        """return number of available objects (thread-safe)."""
        with self._lock:
            return self._allocator.size()
