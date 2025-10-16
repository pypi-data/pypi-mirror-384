"""initialization strategy configuration."""

from enum import Enum, auto


class InitializationStrategy(Enum):
    # purpose: defines when objects in a pool are created.
    # params: none - enum.
    # args: n/a.
    # returns: n/a.
    # raises: n/a.
    """enumeration of pool initialization strategies."""

    EAGER = auto()  # create all objects immediately
    LAZY = auto()  # create objects on-demand
