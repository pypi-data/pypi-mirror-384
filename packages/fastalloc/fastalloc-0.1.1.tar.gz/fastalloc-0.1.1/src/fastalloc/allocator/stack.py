"""lifo stack-based allocator implementation."""

from typing import Generic, List, Optional, TypeVar

T = TypeVar("T")


class StackAllocator(Generic[T]):
    # purpose: manages a stack (last-in-first-out) of free objects for pool to use.
    # params: none for init.
    # args: no arguments needed to create.
    # returns: n/a - initializer.
    # raises: none.
    """lifo (last-in-first-out) stack allocator."""

    # purpose: sets up an empty stack to hold free objects.
    # params: self.
    # args: none.
    # returns: n/a - initializer.
    # raises: none.
    def __init__(self) -> None:
        self._stack: List[T] = []

    # purpose: adds an object to the top of the stack.
    # params: self, obj - the object to add.
    # args: obj required.
    # returns: nothing.
    # raises: none.
    def push(self, obj: T) -> None:
        """push object onto stack."""
        self._stack.append(obj)

    # purpose: removes and returns the top object from the stack.
    # params: self.
    # args: none.
    # returns: object from stack, or None if empty.
    # raises: none.
    def pop(self) -> Optional[T]:
        """pop object from stack."""
        if self._stack:
            return self._stack.pop()
        return None

    # purpose: checks if the stack is empty.
    # params: self.
    # args: none.
    # returns: true if no objects, false otherwise.
    # raises: none.
    def is_empty(self) -> bool:
        """check if stack is empty."""
        return len(self._stack) == 0

    # purpose: tells how many objects are in the stack.
    # params: self.
    # args: none.
    # returns: count of objects.
    # raises: none.
    def size(self) -> int:
        """return number of objects in stack."""
        return len(self._stack)

    # purpose: empties the stack completely.
    # params: self.
    # args: none.
    # returns: nothing.
    # raises: none.
    def clear(self) -> None:
        """clear all objects from stack."""
        self._stack.clear()

    # purpose: creates a nice text representation of the stack for debugging.
    # params: self.
    # args: none.
    # returns: string showing stack size.
    # raises: none.
    def __repr__(self) -> str:
        return f"StackAllocator(size={self.size()})"
