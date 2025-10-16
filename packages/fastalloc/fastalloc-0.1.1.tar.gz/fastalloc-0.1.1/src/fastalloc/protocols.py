"""protocol definitions for fastalloc."""

from typing import Any, ContextManager, Protocol, TypeVar

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


class Resettable(Protocol):
    # purpose: defines what an object needs to support if it can be reset.
    # params: none - protocol definition.
    # args: n/a.
    # returns: n/a.
    # raises: n/a.
    """protocol for objects that support reset operation."""

    # purpose: resets object state to initial clean condition.
    # params: self.
    # args: none.
    # returns: nothing.
    # raises: implementation-specific exceptions.
    def reset(self) -> None:
        """reset the object to initial state."""
        ...


class Allocator(Protocol[T_co]):
    # purpose: defines interface for different allocation strategies.
    # params: generic type T_co.
    # args: n/a - protocol.
    # returns: n/a - protocol.
    # raises: n/a - protocol.
    """protocol for allocator implementations."""

    # purpose: adds an object to the allocator's free list.
    # params: self, obj - object to add.
    # args: obj required.
    # returns: nothing.
    # raises: implementation-specific.
    def push(self, obj: T_co) -> None:
        """add an object to the allocator."""
        ...

    # purpose: retrieves an object from the allocator's free list.
    # params: self.
    # args: none.
    # returns: an object of type T_co, or None if empty.
    # raises: implementation-specific.
    def pop(self) -> T_co | None:
        """retrieve an object from the allocator."""
        ...

    # purpose: checks if allocator has any objects available.
    # params: self.
    # args: none.
    # returns: true if empty, false otherwise.
    # raises: none.
    def is_empty(self) -> bool:
        """check if allocator is empty."""
        ...

    # purpose: tells how many objects are in the allocator.
    # params: self.
    # args: none.
    # returns: integer count.
    # raises: none.
    def size(self) -> int:
        """return number of objects in allocator."""
        ...

    # purpose: removes all objects from the allocator.
    # params: self.
    # args: none.
    # returns: nothing.
    # raises: none.
    def clear(self) -> None:
        """clear all objects from allocator."""
        ...


class Handle(Protocol[T_co], ContextManager[T_co]):
    # purpose: defines interface for pool object handles.
    # params: generic type T_co.
    # args: n/a - protocol.
    # returns: n/a - protocol.
    # raises: n/a - protocol.
    """protocol for pool handle types."""

    # purpose: gets the object this handle is managing.
    # params: self.
    # args: none.
    # returns: the managed object.
    # raises: may raise if handle is invalid.
    def get(self) -> T_co:
        """get the managed object."""
        ...

    # purpose: returns the object back to pool.
    # params: self.
    # args: none.
    # returns: nothing.
    # raises: may raise if already released.
    def release(self) -> None:
        """release the object back to pool."""
        ...
