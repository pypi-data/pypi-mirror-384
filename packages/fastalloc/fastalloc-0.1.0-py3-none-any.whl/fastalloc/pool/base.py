"""base pool abstract class."""

from abc import ABC, abstractmethod
from typing import Callable, Generic, Optional, Type, TypeVar

from ..config.initialization import InitializationStrategy
from ..exceptions import PoolClosedError, PoolConfigurationError
from ..handle.context import ContextHandle
from ..stats.collector import StatsCollector
from ..utils import make_factory, safe_reset, validate_capacity, validate_type

T = TypeVar("T")


class BasePool(ABC, Generic[T]):
    # purpose: base class that all pool types inherit from with common functionality.
    # params: obj_type, capacity, factory, reset_method, enable_statistics, pre_initialize.
    # args: obj_type and capacity required, rest optional.
    # returns: n/a - initializer.
    # raises: PoolConfigurationError for invalid configuration.
    """abstract base class for all pool implementations."""

    # purpose: sets up the basic pool structure.
    # params: self, obj_type - class to pool, capacity - how many objects,
    #         factory - custom creation function, reset_method - method name to reset objects,
    #         enable_statistics - track stats, pre_initialize - create objects eagerly.
    # args: obj_type and capacity required, others keyword-only.
    # returns: n/a - initializer.
    # raises: PoolConfigurationError if settings are invalid.
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
        self._obj_type = obj_type
        self._capacity = validate_capacity(capacity)
        self._factory = factory if factory is not None else make_factory(obj_type)
        self._reset_method = reset_method
        self._closed = False

        # statistics
        self._stats = StatsCollector(enabled=enable_statistics)
        self._stats.update_capacity(self._capacity)

        # initialization
        self._initialization_strategy = (
            InitializationStrategy.EAGER if pre_initialize else InitializationStrategy.LAZY
        )

    # purpose: creates a new object using the factory.
    # params: self.
    # args: none.
    # returns: newly created object.
    # raises: whatever the factory raises.
    def _create_object(self) -> T:
        """create a new object using the factory."""
        return self._factory()

    # purpose: resets an object if it has a reset method.
    # params: self, obj - object to reset.
    # args: obj required.
    # returns: nothing.
    # raises: whatever the reset method raises.
    def _reset_object(self, obj: T) -> None:
        """reset an object if reset method is configured."""
        if self._reset_method:
            if safe_reset(obj, self._reset_method):
                self._stats.record_reset()

    # purpose: validates object is correct type for this pool.
    # params: self, obj - object to check.
    # args: obj required.
    # returns: nothing.
    # raises: TypeMismatchError if wrong type.
    def _validate_object(self, obj: T) -> None:
        """validate object type."""
        validate_type(obj, self._obj_type)

    # purpose: checks if pool is closed and raises error if so.
    # params: self.
    # args: none.
    # returns: nothing.
    # raises: PoolClosedError if pool is closed.
    def _check_closed(self) -> None:
        """check if pool is closed."""
        if self._closed:
            raise PoolClosedError("pool is closed")

    # purpose: gets an object from the pool (must be implemented by subclasses).
    # params: self.
    # args: none.
    # returns: object from pool.
    # raises: PoolEmptyError, PoolClosedError.
    @abstractmethod
    def get(self) -> T:
        """acquire an object from the pool."""
        ...

    # purpose: returns an object to the pool (must be implemented by subclasses).
    # params: self, obj - object to return.
    # args: obj required.
    # returns: nothing.
    # raises: TypeMismatchError, AlreadyReleasedError.
    @abstractmethod
    def release(self, obj: T) -> None:
        """release an object back to the pool."""
        ...

    # purpose: gets object wrapped in context manager for auto-release.
    # params: self.
    # args: none.
    # returns: ContextHandle that auto-releases.
    # raises: PoolEmptyError, PoolClosedError.
    def allocate(self) -> ContextHandle[T]:
        """allocate an object with context manager."""
        obj = self.get()
        return ContextHandle(obj, self.release)

    # purpose: tells how many objects are currently in use.
    # params: self.
    # args: none.
    # returns: count of in-use objects.
    # raises: none.
    def size(self) -> int:
        """return number of objects currently in use."""
        return self._stats.current_in_use

    # purpose: tells total capacity of pool.
    # params: self.
    # args: none.
    # returns: capacity number.
    # raises: none.
    def capacity(self) -> int:
        """return total capacity of the pool."""
        return self._capacity

    # purpose: tells how many objects are free right now.
    # params: self.
    # args: none.
    # returns: count of available objects.
    # raises: none.
    @abstractmethod
    def available(self) -> int:
        """return number of available objects."""
        ...

    # purpose: closes the pool so it can't be used anymore.
    # params: self.
    # args: none.
    # returns: nothing.
    # raises: none.
    def close(self) -> None:
        """close the pool and prevent further allocations."""
        self._closed = True

    # purpose: checks if pool is closed.
    # params: self.
    # args: none.
    # returns: true if closed, false otherwise.
    # raises: none.
    def is_closed(self) -> bool:
        """check if pool is closed."""
        return self._closed

    # purpose: gets the statistics collector.
    # params: self.
    # args: none.
    # returns: StatsCollector instance.
    # raises: none.
    def stats(self) -> StatsCollector:
        """get statistics collector."""
        return self._stats

    # purpose: debug string representation.
    # params: self.
    # args: none.
    # returns: string with pool info.
    # raises: none.
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"type={self._obj_type.__name__}, "
            f"capacity={self._capacity}, "
            f"in_use={self.size()}, "
            f"available={self.available()}, "
            f"closed={self._closed})"
        )
