"""freelist allocator implementation."""

from typing import Generic, List, Optional, TypeVar

T = TypeVar("T")


class FreelistAllocator(Generic[T]):
    # purpose: manages a simple list of free objects, similar to stack but clearer intent.
    # params: none.
    # args: no arguments.
    # returns: n/a - initializer.
    # raises: none.
    """freelist allocator using a list."""

    # purpose: creates an empty freelist to hold available objects.
    # params: self.
    # args: none.
    # returns: n/a - initializer.
    # raises: none.
    def __init__(self) -> None:
        self._freelist: List[T] = []

    # purpose: adds an object to the freelist.
    # params: self, obj - object to add.
    # args: obj required.
    # returns: nothing.
    # raises: none.
    def push(self, obj: T) -> None:
        """add object to freelist."""
        self._freelist.append(obj)

    # purpose: removes and returns an object from the freelist.
    # params: self.
    # args: none.
    # returns: object from freelist, or None if empty.
    # raises: none.
    def pop(self) -> Optional[T]:
        """remove object from freelist."""
        if self._freelist:
            return self._freelist.pop()
        return None

    # purpose: checks if freelist has no objects.
    # params: self.
    # args: none.
    # returns: true if empty, false otherwise.
    # raises: none.
    def is_empty(self) -> bool:
        """check if freelist is empty."""
        return len(self._freelist) == 0

    # purpose: counts how many objects are in the freelist.
    # params: self.
    # args: none.
    # returns: number of objects.
    # raises: none.
    def size(self) -> int:
        """return number of objects in freelist."""
        return len(self._freelist)

    # purpose: removes all objects from the freelist.
    # params: self.
    # args: none.
    # returns: nothing.
    # raises: none.
    def clear(self) -> None:
        """clear all objects from freelist."""
        self._freelist.clear()

    # purpose: gives a string representation for debugging.
    # params: self.
    # args: none.
    # returns: string with freelist size.
    # raises: none.
    def __repr__(self) -> str:
        return f"FreelistAllocator(size={self.size()})"
