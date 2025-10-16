"""context manager handle implementation."""

from typing import Callable, Generic, Optional, TypeVar

from ..exceptions import AlreadyReleasedError

T = TypeVar("T")


class ContextHandle(Generic[T]):
    # purpose: wraps a pooled object so it automatically returns to pool when you're done.
    # params: obj - the object to manage, release_func - function to call when releasing.
    # args: obj and release_func required.
    # returns: n/a - initializer.
    # raises: none.
    """context manager handle that auto-releases object."""

    # purpose: creates a handle for an object with a release callback.
    # params: self, obj - object from pool, release_func - function to release it.
    # args: both required.
    # returns: n/a - initializer.
    # raises: none.
    def __init__(self, obj: T, release_func: Callable[[T], None]) -> None:
        self._obj: Optional[T] = obj
        self._release_func = release_func
        self._released = False

    # purpose: gets the object this handle is managing.
    # params: self.
    # args: none.
    # returns: the managed object.
    # raises: AlreadyReleasedError if already released.
    def get(self) -> T:
        """get the managed object."""
        if self._released or self._obj is None:
            raise AlreadyReleasedError("object has already been released")
        return self._obj

    # purpose: manually returns the object to the pool.
    # params: self.
    # args: none.
    # returns: nothing.
    # raises: AlreadyReleasedError if already released.
    def release(self) -> None:
        """release the object back to pool."""
        if self._released:
            raise AlreadyReleasedError("object has already been released")

        if self._obj is not None:
            self._release_func(self._obj)
            self._obj = None
            self._released = True

    # purpose: lets you use 'with' statement to auto-release when done.
    # params: self.
    # args: none.
    # returns: the managed object.
    # raises: none.
    def __enter__(self) -> T:
        """enter context manager."""
        return self.get()

    # purpose: automatically releases object when exiting 'with' block.
    # params: self, exc_type, exc_val, exc_tb - exception info if any.
    # args: exception info from context manager.
    # returns: None to propagate exceptions.
    # raises: none directly.
    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """exit context manager and release object."""
        if not self._released:
            self.release()

    # purpose: string representation for debugging.
    # params: self.
    # args: none.
    # returns: string showing released state.
    # raises: none.
    def __repr__(self) -> str:
        return f"ContextHandle(released={self._released})"
