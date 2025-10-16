"""fixed-size pool implementation."""

from typing import Callable, Optional, Set, Type, TypeVar

from ..allocator.stack import StackAllocator
from ..config.initialization import InitializationStrategy
from ..exceptions import PoolEmptyError
from ..stats.collector import now_ns
from .base import BasePool

T = TypeVar("T")


class FixedPool(BasePool[T]):
    # purpose: a pool with a fixed size that never grows or shrinks.
    # params: obj_type, capacity, factory, reset_method, enable_statistics, pre_initialize.
    # args: obj_type and capacity required, rest optional.
    # returns: n/a - initializer.
    # raises: PoolConfigurationError if invalid settings.
    """fixed-size pool that never grows."""

    # purpose: creates a fixed pool with the given capacity.
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

        # allocator for free objects
        self._allocator: StackAllocator[T] = StackAllocator()

        # track which objects are in use
        self._in_use: Set[int] = set()

        # pre-initialize if requested
        if self._initialization_strategy == InitializationStrategy.EAGER:
            self._preallocate()

    # purpose: creates all objects up front and puts them in the free list.
    # params: self.
    # args: none.
    # returns: nothing.
    # raises: whatever factory raises.
    def _preallocate(self) -> None:
        """pre-allocate all objects."""
        for _ in range(self._capacity):
            obj = self._create_object()
            self._allocator.push(obj)

    # purpose: gets an object from the pool for you to use.
    # params: self.
    # args: none.
    # returns: object from pool.
    # raises: PoolEmptyError if no objects available, PoolClosedError if closed.
    def get(self) -> T:
        """acquire an object from the pool."""
        self._check_closed()

        start_time = now_ns() if self._stats.enabled else 0

        # try to get from free list
        obj = self._allocator.pop()

        if obj is None:
            # lazy initialization - create new object if under capacity
            if len(self._in_use) < self._capacity:
                obj = self._create_object()
            else:
                raise PoolEmptyError("pool is empty")

        # reset object if needed
        self._reset_object(obj)

        # track in use
        obj_id = id(obj)
        self._in_use.add(obj_id)

        # stats (always record for size() tracking, duration only if enabled)
        duration = now_ns() - start_time if self._stats.enabled else 0
        self._stats.record_allocation(duration)

        return obj

    # purpose: returns an object back to the pool when you're done.
    # params: self, obj - the object to return.
    # args: obj required.
    # returns: nothing.
    # raises: TypeMismatchError if wrong type, AlreadyReleasedError if already returned.
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

    # purpose: tells how many free objects are available right now.
    # params: self.
    # args: none.
    # returns: count of available objects.
    # raises: none.
    def available(self) -> int:
        """return number of available objects."""
        return self._allocator.size()
