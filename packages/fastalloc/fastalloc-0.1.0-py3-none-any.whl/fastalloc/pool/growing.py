"""growing pool implementation."""

from typing import Callable, Optional, Set, Type, TypeVar

from ..allocator.stack import StackAllocator
from ..config.growth_strategy import GrowthConfig, GrowthStrategy
from ..config.initialization import InitializationStrategy
from ..exceptions import PoolEmptyError
from ..stats.collector import now_ns
from ..utils import validate_max_capacity
from .base import BasePool

T = TypeVar("T")


class GrowingPool(BasePool[T]):
    # purpose: a pool that can grow bigger when it runs out of objects.
    # params: obj_type, capacity, max_capacity, growth_config, factory, reset_method,
    #         enable_statistics, pre_initialize.
    # args: obj_type and capacity required, growth_config highly recommended, rest optional.
    # returns: n/a - initializer.
    # raises: PoolConfigurationError for invalid settings.
    """pool that can grow when exhausted."""

    # purpose: creates a pool that grows according to the growth configuration.
    # params: obj_type - class to pool, capacity - starting size, max_capacity - limit,
    #         growth_config - how to grow, other params same as BasePool.
    # args: obj_type and capacity required, rest keyword-only.
    # returns: n/a - initializer.
    # raises: PoolConfigurationError for invalid config.
    def __init__(
        self,
        obj_type: Type[T],
        capacity: int,
        *,
        max_capacity: Optional[int] = None,
        growth_config: Optional[GrowthConfig] = None,
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

        # validate and store max capacity
        self._max_capacity = validate_max_capacity(capacity, max_capacity)

        # default growth config if not provided
        if growth_config is None:
            # default to linear growth by 50% of initial capacity
            from ..config.growth_strategy import linear_growth

            increment = max(1, capacity // 2)
            growth_config = linear_growth(increment, max_capacity=self._max_capacity)

        self._growth_config = growth_config

        # allocator and tracking
        self._allocator: StackAllocator[T] = StackAllocator()
        self._in_use: Set[int] = set()

        # pre-initialize if requested
        if self._initialization_strategy == InitializationStrategy.EAGER:
            self._preallocate()

    # purpose: creates initial objects and puts them in free list.
    # params: self.
    # args: none.
    # returns: nothing.
    # raises: whatever factory raises.
    def _preallocate(self) -> None:
        """pre-allocate initial objects."""
        for _ in range(self._capacity):
            obj = self._create_object()
            self._allocator.push(obj)

    # purpose: makes the pool bigger according to growth strategy.
    # params: self.
    # args: none.
    # returns: nothing.
    # raises: none directly.
    def _grow(self) -> None:
        """grow the pool according to growth strategy."""
        if not self._growth_config.can_grow(self._capacity):
            return

        new_capacity = self._growth_config.calculate_new_capacity(self._capacity)

        # create new objects
        objects_to_add = new_capacity - self._capacity

        for _ in range(objects_to_add):
            obj = self._create_object()
            self._allocator.push(obj)

        # update capacity
        self._capacity = new_capacity
        self._stats.record_growth(new_capacity)

    # purpose: gets an object from pool, growing if needed.
    # params: self.
    # args: none.
    # returns: object from pool.
    # raises: PoolEmptyError if exhausted and can't grow, PoolClosedError if closed.
    def get(self) -> T:
        """acquire an object from the pool."""
        self._check_closed()

        start_time = now_ns() if self._stats.enabled else 0

        # try to get from free list
        obj = self._allocator.pop()

        if obj is None:
            # lazy initialization or growth
            if len(self._in_use) < self._capacity:
                # still under capacity, create new object
                obj = self._create_object()
            else:
                # try to grow
                if self._growth_config.can_grow(self._capacity):
                    self._grow()
                    obj = self._allocator.pop()

                if obj is None:
                    raise PoolEmptyError("pool is empty and cannot grow further")

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

    # purpose: tells how many free objects are available.
    # params: self.
    # args: none.
    # returns: count of available objects.
    # raises: none.
    def available(self) -> int:
        """return number of available objects."""
        return self._allocator.size()

    # purpose: gets the maximum capacity limit.
    # params: self.
    # args: none.
    # returns: max capacity or None if unlimited.
    # raises: none.
    def max_capacity(self) -> Optional[int]:
        """return maximum capacity limit."""
        return self._max_capacity
