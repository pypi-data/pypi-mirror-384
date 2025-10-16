"""owned handle implementation."""

from typing import Callable, Generic, Optional, TypeVar

from ..exceptions import AlreadyReleasedError

T = TypeVar("T")


class OwnedHandle(Generic[T]):
    # purpose: owns an object from pool and ensures it gets returned exactly once.
    # params: obj - the object, release_func - function to release it.
    # args: both required.
    # returns: n/a - initializer.
    # raises: none.
    """handle that owns the pooled object with explicit release."""

    # purpose: creates a handle that owns an object.
    # params: self, obj - the pooled object, release_func - release callback.
    # args: both required.
    # returns: n/a - initializer.
    # raises: none.
    def __init__(self, obj: T, release_func: Callable[[T], None]) -> None:
        self._obj: Optional[T] = obj
        self._release_func = release_func
        self._released = False

    # purpose: gets the object if not released yet.
    # params: self.
    # args: none.
    # returns: the managed object.
    # raises: AlreadyReleasedError if released.
    def get(self) -> T:
        """get the managed object."""
        if self._released or self._obj is None:
            raise AlreadyReleasedError("object has already been released")
        return self._obj

    # purpose: releases object back to pool.
    # params: self.
    # args: none.
    # returns: nothing.
    # raises: AlreadyReleasedError if already done.
    def release(self) -> None:
        """release the object back to pool."""
        if self._released:
            raise AlreadyReleasedError("object has already been released")

        if self._obj is not None:
            self._release_func(self._obj)
            self._obj = None
            self._released = True

    # purpose: checks if object has been released.
    # params: self.
    # args: none.
    # returns: true if released, false otherwise.
    # raises: none.
    def is_released(self) -> bool:
        """check if object has been released."""
        return self._released

    # purpose: automatically releases when handle is deleted.
    # params: self.
    # args: none.
    # returns: nothing.
    # raises: none.
    def __del__(self) -> None:
        """release object when handle is garbage collected."""
        if not self._released and self._obj is not None:
            try:
                self.release()
            except Exception:
                # avoid exceptions in __del__
                pass

    # purpose: debug string representation.
    # params: self.
    # args: none.
    # returns: string showing state.
    # raises: none.
    def __repr__(self) -> str:
        return f"OwnedHandle(released={self._released})"
