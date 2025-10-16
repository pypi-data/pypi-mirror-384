"""growth strategy configuration for pools."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class GrowthStrategy(Enum):
    # purpose: defines how a pool should grow when it needs more capacity.
    # params: none - enum definition.
    # args: n/a.
    # returns: n/a.
    # raises: n/a.
    """enumeration of pool growth strategies."""

    LINEAR = auto()  # grow by fixed increment
    EXPONENTIAL = auto()  # grow by multiplication factor


@dataclass(frozen=True)
class GrowthConfig:
    # purpose: holds settings for how a pool should grow.
    # params: strategy, increment for linear, factor for exponential, max_capacity limit.
    # args: all as dataclass fields.
    # returns: n/a - dataclass.
    # raises: none at creation, validation happens elsewhere.
    """configuration for pool growth behavior."""

    strategy: GrowthStrategy
    increment: Optional[int] = None  # for linear growth
    factor: Optional[float] = None  # for exponential growth
    max_capacity: Optional[int] = None

    # purpose: calculates the new capacity after growth.
    # params: self, current_capacity - how big the pool is now.
    # args: current_capacity required.
    # returns: new capacity as integer.
    # raises: ValueError if configuration is invalid for strategy.
    def calculate_new_capacity(self, current_capacity: int) -> int:
        """calculate new capacity based on growth strategy."""
        if self.strategy == GrowthStrategy.LINEAR:
            if self.increment is None or self.increment <= 0:
                raise ValueError("linear growth requires positive increment")
            new_capacity = current_capacity + self.increment

        elif self.strategy == GrowthStrategy.EXPONENTIAL:
            if self.factor is None or self.factor <= 1.0:
                raise ValueError("exponential growth requires factor > 1.0")
            new_capacity = int(current_capacity * self.factor)
            # ensure at least +1 growth
            if new_capacity <= current_capacity:
                new_capacity = current_capacity + 1

        else:
            raise ValueError(f"unknown growth strategy: {self.strategy}")

        # clamp to max_capacity if set
        if self.max_capacity is not None:
            new_capacity = min(new_capacity, self.max_capacity)

        return new_capacity

    # purpose: checks if pool can still grow.
    # params: self, current_capacity - current size.
    # args: current_capacity required.
    # returns: true if can grow, false if at max.
    # raises: none.
    def can_grow(self, current_capacity: int) -> bool:
        """check if pool can grow from current capacity."""
        if self.max_capacity is None:
            return True
        return current_capacity < self.max_capacity


# purpose: creates a linear growth configuration.
# params: increment - how much to add each time, max_capacity - optional limit.
# args: increment required, max_capacity optional.
# returns: GrowthConfig configured for linear growth.
# raises: ValueError if increment is invalid.
def linear_growth(increment: int, max_capacity: Optional[int] = None) -> GrowthConfig:
    """create linear growth configuration."""
    if increment <= 0:
        raise ValueError(f"increment must be positive, got {increment}")
    return GrowthConfig(
        strategy=GrowthStrategy.LINEAR,
        increment=increment,
        max_capacity=max_capacity,
    )


# purpose: creates an exponential growth configuration.
# params: factor - multiplier for growth, max_capacity - optional limit.
# args: factor required, max_capacity optional.
# returns: GrowthConfig configured for exponential growth.
# raises: ValueError if factor is invalid.
def exponential_growth(factor: float, max_capacity: Optional[int] = None) -> GrowthConfig:
    """create exponential growth configuration."""
    if factor <= 1.0:
        raise ValueError(f"factor must be > 1.0, got {factor}")
    return GrowthConfig(
        strategy=GrowthStrategy.EXPONENTIAL,
        factor=factor,
        max_capacity=max_capacity,
    )
