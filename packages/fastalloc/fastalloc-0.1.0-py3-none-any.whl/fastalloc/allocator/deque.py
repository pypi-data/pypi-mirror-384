"""deque-based allocator implementation."""

from collections import deque
from typing import Deque, Generic, Optional, TypeVar

T = TypeVar("T")


class DequeAllocator(Generic[T]):
    # purpose: manages free objects using a deque for efficient both-ends operations.
    # params: none.
    # args: no arguments.
    # returns: n/a - initializer.
    # raises: none.
    """allocator using collections.deque for efficient operations."""

    # purpose: creates an empty deque to store free objects.
    # params: self.
    # args: none.
    # returns: n/a - initializer.
    # raises: none.
    def __init__(self) -> None:
        self._deque: Deque[T] = deque()

    # purpose: adds an object to the deque.
    # params: self, obj - object to add.
    # args: obj required.
    # returns: nothing.
    # raises: none.
    def push(self, obj: T) -> None:
        """add object to deque."""
        self._deque.append(obj)

    # purpose: removes and returns an object from the deque.
    # params: self.
    # args: none.
    # returns: object from deque, or None if empty.
    # raises: none.
    def pop(self) -> Optional[T]:
        """remove object from deque."""
        if self._deque:
            return self._deque.pop()
        return None

    # purpose: checks if the deque is empty.
    # params: self.
    # args: none.
    # returns: true if empty, false otherwise.
    # raises: none.
    def is_empty(self) -> bool:
        """check if deque is empty."""
        return len(self._deque) == 0

    # purpose: counts objects in the deque.
    # params: self.
    # args: none.
    # returns: number of objects.
    # raises: none.
    def size(self) -> int:
        """return number of objects in deque."""
        return len(self._deque)

    # purpose: empties the entire deque.
    # params: self.
    # args: none.
    # returns: nothing.
    # raises: none.
    def clear(self) -> None:
        """clear all objects from deque."""
        self._deque.clear()

    # purpose: creates debug string showing deque size.
    # params: self.
    # args: none.
    # returns: string representation.
    # raises: none.
    def __repr__(self) -> str:
        return f"DequeAllocator(size={self.size()})"
