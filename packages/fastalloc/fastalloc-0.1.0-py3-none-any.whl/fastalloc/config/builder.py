"""builder pattern for pool configuration."""

from typing import Callable, Generic, Optional, Type, TypeVar, Union

from ..exceptions import PoolConfigurationError
from ..pool.fixed import FixedPool
from ..pool.growing import GrowingPool
from ..pool.thread_local import ThreadLocalPool
from ..pool.thread_safe import ThreadSafePool
from .growth_strategy import GrowthConfig, GrowthStrategy

T = TypeVar("T")


class PoolBuilder(Generic[T]):
    # purpose: helps you build a pool step by step with a nice fluent interface.
    # params: none initially, then set via methods.
    # args: none.
    # returns: n/a - initializer.
    # raises: none.
    """fluent builder for pool configuration."""

    # purpose: starts building a pool with empty configuration.
    # params: self.
    # args: none.
    # returns: n/a - initializer.
    # raises: none.
    def __init__(self) -> None:
        self._obj_type: Optional[Type[T]] = None
        self._capacity: Optional[int] = None
        self._max_capacity: Optional[int] = None
        self._growth_strategy: Optional[GrowthStrategy] = None
        self._growth_increment: Optional[int] = None
        self._growth_factor: Optional[float] = None
        self._factory: Optional[Callable[[], T]] = None
        self._reset_method: Optional[str] = None
        self._enable_statistics: bool = False
        self._pre_initialize: bool = False
        self._thread_safe: bool = False
        self._thread_local: bool = False

    # purpose: sets the type of objects the pool will manage.
    # params: self, obj_type - the class to pool.
    # args: obj_type required.
    # returns: self for chaining.
    # raises: none.
    def type(self, obj_type: Type[T]) -> "PoolBuilder[T]":
        """set the object type for the pool."""
        self._obj_type = obj_type
        return self

    # purpose: sets the initial capacity of the pool.
    # params: self, capacity - how many objects.
    # args: capacity required.
    # returns: self for chaining.
    # raises: none.
    def capacity(self, capacity: int) -> "PoolBuilder[T]":
        """set the initial capacity."""
        self._capacity = capacity
        return self

    # purpose: sets the maximum capacity limit for growing pools.
    # params: self, max_capacity - the upper limit.
    # args: max_capacity required.
    # returns: self for chaining.
    # raises: none.
    def max_capacity(self, max_capacity: int) -> "PoolBuilder[T]":
        """set the maximum capacity."""
        self._max_capacity = max_capacity
        return self

    # purpose: configures how the pool should grow.
    # params: self, strategy - LINEAR or EXPONENTIAL, increment - for linear,
    #         factor - for exponential.
    # args: strategy required, increment and factor optional depending on strategy.
    # returns: self for chaining.
    # raises: none.
    def growth_strategy(
        self,
        strategy: GrowthStrategy,
        increment: Optional[int] = None,
        factor: Optional[float] = None,
    ) -> "PoolBuilder[T]":
        """set the growth strategy."""
        self._growth_strategy = strategy
        self._growth_increment = increment
        self._growth_factor = factor
        return self

    # purpose: sets whether to create all objects immediately.
    # params: self, pre_initialize - true to create eagerly.
    # args: pre_initialize required.
    # returns: self for chaining.
    # raises: none.
    def pre_initialize(self, pre_initialize: bool) -> "PoolBuilder[T]":
        """set pre-initialization strategy."""
        self._pre_initialize = pre_initialize
        return self

    # purpose: sets a custom factory function for creating objects.
    # params: self, factory - callable that creates instances.
    # args: factory required.
    # returns: self for chaining.
    # raises: none.
    def factory(self, factory: Callable[[], T]) -> "PoolBuilder[T]":
        """set custom factory function."""
        self._factory = factory
        return self

    # purpose: sets the method name to call for resetting objects.
    # params: self, method_name - name of reset method.
    # args: method_name required.
    # returns: self for chaining.
    # raises: none.
    def reset_method(self, method_name: str) -> "PoolBuilder[T]":
        """set reset method name."""
        self._reset_method = method_name
        return self

    # purpose: enables or disables statistics collection.
    # params: self, enable - true to collect stats.
    # args: enable required.
    # returns: self for chaining.
    # raises: none.
    def enable_statistics(self, enable: bool) -> "PoolBuilder[T]":
        """enable statistics collection."""
        self._enable_statistics = enable
        return self

    # purpose: makes the pool thread-safe with locks.
    # params: self, thread_safe - true for thread safety.
    # args: thread_safe required.
    # returns: self for chaining.
    # raises: none.
    def thread_safe(self, thread_safe: bool) -> "PoolBuilder[T]":
        """make pool thread-safe."""
        self._thread_safe = thread_safe
        return self

    # purpose: makes the pool thread-local (per-thread pools).
    # params: self, thread_local - true for thread-local.
    # args: thread_local required.
    # returns: self for chaining.
    # raises: none.
    def thread_local(self, thread_local: bool) -> "PoolBuilder[T]":
        """make pool thread-local."""
        self._thread_local = thread_local
        return self

    # purpose: validates configuration and builds the final pool.
    # params: self.
    # args: none.
    # returns: configured pool instance.
    # raises: PoolConfigurationError if configuration is invalid.
    def build(self) -> Union[FixedPool[T], GrowingPool[T], ThreadSafePool[T], ThreadLocalPool[T]]:
        """build the pool with current configuration."""
        # validate required fields
        if self._obj_type is None:
            raise PoolConfigurationError("object type is required")
        if self._capacity is None:
            raise PoolConfigurationError("capacity is required")

        # validate thread safety conflicts
        if self._thread_safe and self._thread_local:
            raise PoolConfigurationError("cannot be both thread-safe and thread-local")

        # common kwargs
        common_kwargs = {
            "factory": self._factory,
            "reset_method": self._reset_method,
            "enable_statistics": self._enable_statistics,
            "pre_initialize": self._pre_initialize,
        }

        # determine pool type
        if self._thread_local:
            return ThreadLocalPool(
                self._obj_type,
                self._capacity,
                **common_kwargs,
            )
        elif self._thread_safe:
            return ThreadSafePool(
                self._obj_type,
                self._capacity,
                **common_kwargs,
            )
        elif self._growth_strategy is not None:
            # growing pool
            growth_config = self._build_growth_config()
            return GrowingPool(
                self._obj_type,
                self._capacity,
                max_capacity=self._max_capacity,
                growth_config=growth_config,
                **common_kwargs,
            )
        else:
            # fixed pool
            return FixedPool(
                self._obj_type,
                self._capacity,
                **common_kwargs,
            )

    # purpose: creates the growth configuration object from builder settings.
    # params: self.
    # args: none.
    # returns: GrowthConfig instance.
    # raises: PoolConfigurationError if growth settings invalid.
    def _build_growth_config(self) -> GrowthConfig:
        """build growth configuration."""
        if self._growth_strategy is None:
            raise PoolConfigurationError("growth strategy not set")

        if self._growth_strategy == GrowthStrategy.LINEAR:
            if self._growth_increment is None:
                raise PoolConfigurationError("linear growth requires increment")
            from .growth_strategy import linear_growth

            return linear_growth(self._growth_increment, self._max_capacity)

        elif self._growth_strategy == GrowthStrategy.EXPONENTIAL:
            if self._growth_factor is None:
                raise PoolConfigurationError("exponential growth requires factor")
            from .growth_strategy import exponential_growth

            return exponential_growth(self._growth_factor, self._max_capacity)

        else:
            raise PoolConfigurationError(f"unknown growth strategy: {self._growth_strategy}")
