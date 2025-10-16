"""exception types for fastalloc."""

from typing import Any


class FastAllocError(Exception):
    # purpose: the main error class that all other fastalloc errors inherit from.
    # params: none specific - standard exception initialization.
    # args: takes a message string to describe what went wrong.
    # returns: n/a - this is an exception class.
    # raises: n/a - this is raised, not calling other exceptions.
    """base exception for all fastalloc errors."""
    pass


class PoolEmptyError(FastAllocError):
    # purpose: raised when you try to get an object but the pool has no more left.
    # params: none specific.
    # args: optionally takes a message describing the empty pool situation.
    # returns: n/a - exception class.
    # raises: n/a.
    """raised when pool is exhausted and cannot provide an object."""
    pass


class PoolClosedError(FastAllocError):
    # purpose: raised when you try to use a pool that has been closed/shut down.
    # params: none specific.
    # args: optionally takes a message about the closed pool.
    # returns: n/a - exception class.
    # raises: n/a.
    """raised when attempting to use a closed pool."""
    pass


class TypeMismatchError(FastAllocError):
    # purpose: raised when you try to return an object to a pool but it's the wrong type.
    # params: expected_type and actual_type can be passed to help debugging.
    # args: message, expected type, actual type.
    # returns: n/a - exception class.
    # raises: n/a.
    """raised when releasing an object of wrong type to a pool."""

    # purpose: sets up the error with info about what type was expected vs what was given.
    # params: expected_type - the type the pool wants, actual_type - what you tried to give,
    #         message - optional custom message.
    # args: all are keyword arguments for clarity.
    # returns: n/a - initializer.
    # raises: n/a.
    def __init__(
        self,
        expected_type: type,
        actual_type: type,
        message: str = "",
    ) -> None:
        self.expected_type = expected_type
        self.actual_type = actual_type
        if not message:
            message = (
                f"type mismatch: expected {expected_type.__name__}, " f"got {actual_type.__name__}"
            )
        super().__init__(message)


class InvalidCapacityError(FastAllocError):
    # purpose: raised when you try to create a pool with a bad capacity number.
    # params: capacity value that was invalid.
    # args: the bad capacity value and optional message.
    # returns: n/a - exception class.
    # raises: n/a.
    """raised when capacity configuration is invalid."""

    # purpose: sets up the error with the bad capacity value.
    # params: capacity - the invalid number, message - optional explanation.
    # args: capacity required, message optional.
    # returns: n/a - initializer.
    # raises: n/a.
    def __init__(self, capacity: Any, message: str = "") -> None:
        self.capacity = capacity
        if not message:
            message = f"invalid capacity: {capacity}"
        super().__init__(message)


class AlreadyReleasedError(FastAllocError):
    # purpose: raised when you try to return an object to the pool twice.
    # params: none specific.
    # args: optional message describing the double-release attempt.
    # returns: n/a - exception class.
    # raises: n/a.
    """raised when attempting to release an object that was already released."""
    pass


class PoolConfigurationError(FastAllocError):
    # purpose: raised when pool configuration has invalid or conflicting settings.
    # params: none specific.
    # args: message describing what's wrong with the configuration.
    # returns: n/a - exception class.
    # raises: n/a.
    """raised when pool configuration is invalid or inconsistent."""
    pass
