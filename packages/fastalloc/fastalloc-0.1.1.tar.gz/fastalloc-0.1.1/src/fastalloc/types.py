"""type aliases and type definitions for fastalloc."""

import sys
from typing import Any, Callable, Protocol, TypeVar, Union

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

# type variable for pool object types
T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)

# factory function type - callable that creates instances of type T
Factory: TypeAlias = Callable[[], T]

# reset function type - callable that takes an instance and resets it
ResetFunction: TypeAlias = Callable[[T], None]

# capacity type - positive integer
Capacity: TypeAlias = int

# type for statistics snapshots
StatsDict: TypeAlias = dict[str, Union[int, float, str]]


class Resettable(Protocol):
    # purpose: defines what objects need to have if they can be reset/cleaned.
    # params: none - this is a protocol definition.
    # args: n/a - protocol.
    # returns: n/a - protocol.
    # raises: n/a - protocol.
    """protocol for objects that can be reset to initial state."""

    # purpose: resets the object back to a clean state so it can be reused.
    # params: self - the object being reset.
    # args: just self, no other arguments.
    # returns: nothing, just changes the object in-place.
    # raises: might raise if reset fails, depends on implementation.
    def reset(self) -> None:
        """reset object to initial state."""
        ...


class PoolProtocol(Protocol[T_co]):
    # purpose: defines the interface that all pool types must provide.
    # params: generic type T_co for the objects in the pool.
    # args: n/a - protocol.
    # returns: n/a - protocol.
    # raises: n/a - protocol.
    """protocol defining the pool interface."""

    # purpose: gets an object from the pool for you to use.
    # params: self - the pool instance.
    # args: no arguments.
    # returns: an object of type T_co from the pool.
    # raises: PoolEmptyError if no objects available, PoolClosedError if pool is closed.
    def get(self) -> T_co:
        """acquire an object from the pool."""
        ...

    # purpose: returns an object back to the pool when you're done with it.
    # params: self - the pool, obj - the object to return.
    # args: obj is required.
    # returns: nothing.
    # raises: TypeMismatchError if wrong type, AlreadyReleasedError if already returned.
    def release(self, obj: T_co) -> None:
        """release an object back to the pool."""
        ...

    # purpose: tells you how many objects are currently being used.
    # params: self - the pool.
    # args: none.
    # returns: integer count of objects in use.
    # raises: none.
    def size(self) -> int:
        """return number of objects currently in use."""
        ...

    # purpose: tells you the total capacity of the pool.
    # params: self - the pool.
    # args: none.
    # returns: integer total capacity.
    # raises: none.
    def capacity(self) -> int:
        """return total capacity of the pool."""
        ...

    # purpose: tells you how many free objects are available right now.
    # params: self - the pool.
    # args: none.
    # returns: integer count of available objects.
    # raises: none.
    def available(self) -> int:
        """return number of available objects."""
        ...

    # purpose: shuts down the pool so it can't be used anymore.
    # params: self - the pool.
    # args: none.
    # returns: nothing.
    # raises: none.
    def close(self) -> None:
        """close the pool and prevent further allocations."""
        ...
