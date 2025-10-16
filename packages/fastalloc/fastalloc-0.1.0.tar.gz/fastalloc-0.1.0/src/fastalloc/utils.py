"""utility functions for fastalloc."""

import weakref
from typing import Any, Callable, Optional, Type, TypeVar

from .exceptions import TypeMismatchError

T = TypeVar("T")


# purpose: checks if a class uses __slots__ for memory optimization.
# params: cls - the class to check.
# args: cls is required.
# returns: true if class uses slots, false otherwise.
# raises: none.
def has_slots(cls: Type[Any]) -> bool:
    """check if a class uses __slots__."""
    return hasattr(cls, "__slots__")


# purpose: validates that an object is the correct type for a pool.
# params: obj - object to check, expected_type - what type it should be.
# args: both obj and expected_type required.
# returns: nothing if valid.
# raises: TypeMismatchError if types don't match.
def validate_type(obj: Any, expected_type: Type[T]) -> None:
    """validate object type matches expected type."""
    if not isinstance(obj, expected_type):
        raise TypeMismatchError(
            expected_type=expected_type,
            actual_type=type(obj),
        )


# purpose: safely calls a reset method on an object if it has one.
# params: obj - object to reset, method_name - name of reset method (default 'reset').
# args: obj required, method_name optional with default.
# returns: true if reset was called, false if method didn't exist.
# raises: any exception the reset method itself raises.
def safe_reset(obj: Any, method_name: str = "reset") -> bool:
    """safely call reset method on object if it exists."""
    reset_method = getattr(obj, method_name, None)
    if reset_method is not None and callable(reset_method):
        reset_method()
        return True
    return False


# purpose: creates a factory function for a class with optional arguments.
# params: cls - the class to instantiate, args - positional args, kwargs - keyword args.
# args: cls required, args and kwargs optional.
# returns: a function that creates instances of cls.
# raises: none directly, but returned function may raise.
def make_factory(
    cls: Type[T],
    *args: Any,
    **kwargs: Any,
) -> Callable[[], T]:
    """create a factory function for a class with given arguments."""

    # purpose: the actual factory that creates instances.
    # params: none - captures cls, args, kwargs from outer scope.
    # args: none.
    # returns: new instance of cls.
    # raises: whatever cls.__init__ might raise.
    def factory() -> T:
        return cls(*args, **kwargs)

    return factory


# purpose: creates a weak reference to an object if possible.
# params: obj - object to create weak reference for, callback - optional callback on deletion.
# args: obj required, callback optional.
# returns: weak reference to obj, or None if not possible.
# raises: none.
def try_weakref(
    obj: T,
    callback: Optional[Callable[[weakref.ReferenceType[T]], None]] = None,
) -> Optional[weakref.ReferenceType[T]]:
    """attempt to create a weak reference to an object."""
    try:
        return weakref.ref(obj, callback)
    except TypeError:
        # object doesn't support weak references
        return None


# purpose: checks if two objects are the exact same object in memory.
# params: obj1, obj2 - objects to compare.
# args: both required.
# returns: true if same object, false otherwise.
# raises: none.
def is_same_object(obj1: Any, obj2: Any) -> bool:
    """check if two references point to the same object."""
    return obj1 is obj2


# purpose: gets the memory address of an object as an integer.
# params: obj - the object.
# args: obj required.
# returns: integer memory address.
# raises: none.
def object_id(obj: Any) -> int:
    """get unique identifier for an object."""
    return id(obj)


# purpose: validates that a capacity value is valid (positive integer).
# params: capacity - the value to check, name - name of the parameter for errors.
# args: capacity required, name optional.
# returns: the capacity value unchanged if valid.
# raises: ValueError if capacity is invalid.
def validate_capacity(capacity: int, name: str = "capacity") -> int:
    """validate that capacity is a positive integer."""
    if not isinstance(capacity, int):
        raise ValueError(f"{name} must be an integer, got {type(capacity).__name__}")
    if capacity <= 0:
        raise ValueError(f"{name} must be positive, got {capacity}")
    return capacity


# purpose: validates that max_capacity is valid and greater than initial capacity.
# params: initial - starting capacity, maximum - max capacity (optional).
# args: initial required, maximum optional.
# returns: the maximum value if valid, or None if not provided.
# raises: ValueError if maximum is invalid or less than initial.
def validate_max_capacity(initial: int, maximum: Optional[int]) -> Optional[int]:
    """validate max_capacity is greater than initial capacity."""
    if maximum is None:
        return None

    if not isinstance(maximum, int):
        raise ValueError(f"max_capacity must be an integer, got {type(maximum).__name__}")

    if maximum <= initial:
        raise ValueError(
            f"max_capacity ({maximum}) must be greater than capacity ({initial})"
        )

    return maximum


# purpose: clamps a value between min and max bounds.
# params: value - value to clamp, minimum - lower bound, maximum - upper bound.
# args: all required.
# returns: clamped value.
# raises: none.
def clamp(value: int, minimum: int, maximum: int) -> int:
    """clamp value between minimum and maximum."""
    return max(minimum, min(value, maximum))
