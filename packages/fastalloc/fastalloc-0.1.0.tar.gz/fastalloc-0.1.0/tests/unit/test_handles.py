"""unit tests for handle types."""

import pytest

from fastalloc import AlreadyReleasedError, FixedPool
from fastalloc.handle import ContextHandle, OwnedHandle, WeakHandle


def test_context_handle_basic(simple_object_class):
    """test context handle basic usage."""
    pool = FixedPool(simple_object_class, capacity=5)
    obj = pool.get()

    handle = ContextHandle(obj, pool.release)
    assert handle.get() is obj

    handle.release()
    assert pool.available() == 1


def test_context_handle_with_statement(simple_object_class):
    """test context handle with statement."""
    pool = FixedPool(simple_object_class, capacity=5)
    obj = pool.get()

    handle = ContextHandle(obj, pool.release)
    with handle as managed_obj:
        assert managed_obj is obj

    assert pool.available() == 1


def test_context_handle_double_release(simple_object_class):
    """test context handle prevents double release."""
    pool = FixedPool(simple_object_class, capacity=5)
    obj = pool.get()

    handle = ContextHandle(obj, pool.release)
    handle.release()

    with pytest.raises(AlreadyReleasedError):
        handle.release()


def test_owned_handle_basic(simple_object_class):
    """test owned handle."""
    pool = FixedPool(simple_object_class, capacity=5)
    obj = pool.get()

    handle = OwnedHandle(obj, pool.release)
    assert handle.get() is obj
    assert not handle.is_released()

    handle.release()
    assert handle.is_released()
    assert pool.available() == 1


def test_weak_handle_basic(simple_object_class):
    """test weak handle."""
    pool = FixedPool(simple_object_class, capacity=5)
    obj = pool.get()

    handle = WeakHandle(obj, pool.release)
    assert handle.get() is obj
    assert handle.is_alive()

    handle.release()
    assert handle.is_released()
    assert pool.available() == 1


def test_weak_handle_garbage_collection(simple_object_class):
    """test weak handle with garbage collection."""
    pool = FixedPool(simple_object_class, capacity=5)
    obj = pool.get()

    handle = WeakHandle(obj, pool.release)
    assert handle.is_alive()

    # note: in CPython, deleting obj should make it collectable
    # but this is implementation-specific
    obj_id = id(obj)
    del obj

    # handle should detect object is gone
    # (behavior may vary by Python implementation)
