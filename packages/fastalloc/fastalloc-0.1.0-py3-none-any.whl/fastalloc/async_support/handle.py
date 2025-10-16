"""async context manager handle."""

from typing import Callable, Generic, Optional, TypeVar

from ..exceptions import AlreadyReleasedError

T = TypeVar("T")


class AsyncContextHandle(Generic[T]):
    # purpose: wraps a pooled object for async with statement so it auto-releases.
    # params: obj - the object to manage, release_func - async function to release.
    # args: both required.
    # returns: n/a - initializer.
    # raises: none.
    """async context manager handle for pooled objects."""

    # purpose: creates async handle for an object.
    # params: self, obj - object from pool, release_func - async release function.
    # args: both required.
    # returns: n/a - initializer.
    # raises: none.
    def __init__(self, obj: T, release_func: Callable[[T], None]) -> None:
        self._obj: Optional[T] = obj
        self._release_func = release_func
        self._released = False

    # purpose: gets the managed object.
    # params: self.
    # args: none.
    # returns: the object.
    # raises: AlreadyReleasedError if released.
    def get(self) -> T:
        """get the managed object."""
        if self._released or self._obj is None:
            raise AlreadyReleasedError("object has already been released")
        return self._obj

    # purpose: releases object back to pool (non-async version).
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

    # purpose: enters async with block and gives you the object.
    # params: self.
    # args: none.
    # returns: the managed object (awaitable).
    # raises: none.
    async def __aenter__(self) -> T:
        """enter async context manager."""
        return self.get()

    # purpose: exits async with block and releases object.
    # params: self, exc_type, exc_val, exc_tb - exception info if any.
    # args: exception info from async context.
    # returns: nothing (awaitable).
    # raises: none directly.
    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """exit async context manager and release object."""
        if not self._released:
            self.release()

    # purpose: debug string representation.
    # params: self.
    # args: none.
    # returns: string with state.
    # raises: none.
    def __repr__(self) -> str:
        return f"AsyncContextHandle(released={self._released})"
