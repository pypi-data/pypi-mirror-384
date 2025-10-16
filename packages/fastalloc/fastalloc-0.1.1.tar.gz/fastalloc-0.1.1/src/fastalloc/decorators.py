"""decorators for fastalloc."""

from typing import Any, Callable, Optional, Type, TypeVar, Union

from .config.growth_strategy import GrowthConfig, GrowthStrategy
from .pool.fixed import FixedPool
from .pool.growing import GrowingPool
from .pool.thread_local import ThreadLocalPool
from .pool.thread_safe import ThreadSafePool

T = TypeVar("T")


# purpose: decorator that attaches a pool to a class so you can use it easily.
# params: capacity - pool size, thread_safe - use locking, thread_local - per-thread pools,
#         max_capacity - growth limit, growth_strategy - how to grow, pre_initialize - eager,
#         reset_method - method to reset objects.
# args: capacity required, rest optional keyword arguments.
# returns: decorator function.
# raises: none directly, but pool creation might raise.
def pooled(
    capacity: int,
    *,
    thread_safe: bool = False,
    thread_local: bool = False,
    max_capacity: Optional[int] = None,
    growth_strategy: Optional[Union[GrowthStrategy, GrowthConfig]] = None,
    pre_initialize: bool = False,
    reset_method: Optional[str] = None,
    enable_statistics: bool = False,
) -> Callable[[Type[T]], Type[T]]:
    """decorator to attach a pool to a class."""

    # purpose: the actual decorator that wraps the class.
    # params: cls - the class to decorate.
    # args: cls required.
    # returns: the class with .pool attribute added.
    # raises: ValueError if configuration is invalid.
    def decorator(cls: Type[T]) -> Type[T]:
        """attach pool to class."""
        # validate
        if thread_safe and thread_local:
            raise ValueError("cannot be both thread_safe and thread_local")

        # common kwargs
        common_kwargs = {
            "factory": None,  # use default constructor
            "reset_method": reset_method,
            "enable_statistics": enable_statistics,
            "pre_initialize": pre_initialize,
        }

        # create appropriate pool type
        pool: Union[FixedPool[T], GrowingPool[T], ThreadSafePool[T], ThreadLocalPool[T]]

        if thread_local:
            pool = ThreadLocalPool(cls, capacity, **common_kwargs)
        elif thread_safe:
            pool = ThreadSafePool(cls, capacity, **common_kwargs)
        elif growth_strategy is not None:
            # growing pool
            if isinstance(growth_strategy, GrowthConfig):
                growth_config = growth_strategy
            elif isinstance(growth_strategy, GrowthStrategy):
                # create default config for strategy
                if growth_strategy == GrowthStrategy.LINEAR:
                    from .config.growth_strategy import linear_growth

                    increment = max(1, capacity // 2)
                    growth_config = linear_growth(increment, max_capacity)
                elif growth_strategy == GrowthStrategy.EXPONENTIAL:
                    from .config.growth_strategy import exponential_growth

                    growth_config = exponential_growth(2.0, max_capacity)
                else:
                    raise ValueError(f"unknown growth strategy: {growth_strategy}")
            else:
                raise ValueError("growth_strategy must be GrowthStrategy or GrowthConfig")

            pool = GrowingPool(
                cls,
                capacity,
                max_capacity=max_capacity,
                growth_config=growth_config,
                **common_kwargs,
            )
        else:
            # fixed pool
            pool = FixedPool(cls, capacity, **common_kwargs)

        # attach pool to class
        cls.pool = pool  # type: ignore

        return cls

    return decorator
