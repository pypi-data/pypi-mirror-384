"""weak reference handle implementation."""

import weakref
from typing import Callable, Generic, Optional, TypeVar

from ..exceptions import AlreadyReleasedError

T = TypeVar("T")


class WeakHandle(Generic[T]):
    # purpose: holds a weak reference to pooled object so it doesn't prevent garbage collection.
    # params: obj - object to reference weakly, release_func - release callback.
    # args: both required.
    # returns: n/a - initializer.
    # raises: TypeError if object doesn't support weak references.
    """handle using weak reference to pooled object."""

    # purpose: creates a weak handle that doesn't keep object alive.
    # params: self, obj - the object, release_func - function to release.
    # args: both required.
    # returns: n/a - initializer.
    # raises: TypeError if obj doesn't support weakrefs.
    def __init__(self, obj: T, release_func: Callable[[T], None]) -> None:
        self._ref: weakref.ReferenceType[T] = weakref.ref(obj, self._on_finalize)
        self._release_func = release_func
        self._released = False

    # purpose: callback when the object gets garbage collected.
    # params: self, ref - the weak reference that died.
    # args: ref from weakref system.
    # returns: nothing.
    # raises: none.
    def _on_finalize(self, ref: weakref.ReferenceType[T]) -> None:
        """callback when referenced object is finalized."""
        # object was garbage collected, mark as released
        self._released = True

    # purpose: gets the object if it still exists.
    # params: self.
    # args: none.
    # returns: the object.
    # raises: AlreadyReleasedError if released or object was collected.
    def get(self) -> T:
        """get the managed object."""
        if self._released:
            raise AlreadyReleasedError("object has already been released")

        obj = self._ref()
        if obj is None:
            raise AlreadyReleasedError("object has been garbage collected")

        return obj

    # purpose: releases the object back to pool.
    # params: self.
    # args: none.
    # returns: nothing.
    # raises: AlreadyReleasedError if already done or object collected.
    def release(self) -> None:
        """release the object back to pool."""
        if self._released:
            raise AlreadyReleasedError("object has already been released")

        obj = self._ref()
        if obj is None:
            # object was already garbage collected
            self._released = True
            return

        self._release_func(obj)
        self._released = True

    # purpose: checks if released or object collected.
    # params: self.
    # args: none.
    # returns: true if released, false if still valid.
    # raises: none.
    def is_released(self) -> bool:
        """check if object has been released."""
        return self._released

    # purpose: checks if the referenced object is still alive.
    # params: self.
    # args: none.
    # returns: true if object exists, false if collected.
    # raises: none.
    def is_alive(self) -> bool:
        """check if referenced object is still alive."""
        return self._ref() is not None and not self._released

    # purpose: debug string.
    # params: self.
    # args: none.
    # returns: string with state info.
    # raises: none.
    def __repr__(self) -> str:
        return f"WeakHandle(released={self._released}, alive={self.is_alive()})"
