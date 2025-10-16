"""unit tests for fixed pool."""

import pytest

from fastalloc import FixedPool, PoolClosedError, PoolEmptyError
from fastalloc.exceptions import AlreadyReleasedError, TypeMismatchError


def test_fixed_pool_creation(simple_object_class, capacity):
    """test creating a fixed pool."""
    pool = FixedPool(simple_object_class, capacity)
    assert pool.capacity() == capacity
    assert pool.size() == 0
    assert pool.available() == 0


def test_fixed_pool_get_and_release(simple_object_class, capacity):
    """test basic get and release."""
    pool = FixedPool(simple_object_class, capacity)

    obj = pool.get()
    assert isinstance(obj, simple_object_class)
    assert pool.size() == 1
    assert pool.available() == 0

    pool.release(obj)
    assert pool.size() == 0
    assert pool.available() == 1


def test_fixed_pool_exhaustion(simple_object_class):
    """test pool raises error when exhausted."""
    pool = FixedPool(simple_object_class, capacity=2)

    obj1 = pool.get()
    obj2 = pool.get()

    with pytest.raises(PoolEmptyError):
        pool.get()

    pool.release(obj1)
    obj3 = pool.get()  # should work now
    assert obj3 is obj1  # should reuse


def test_fixed_pool_context_manager(simple_object_class, capacity):
    """test context manager allocate."""
    pool = FixedPool(simple_object_class, capacity)

    with pool.allocate() as obj:
        assert isinstance(obj, simple_object_class)
        assert pool.size() == 1

    assert pool.size() == 0
    assert pool.available() == 1


def test_fixed_pool_pre_initialize(simple_object_class, capacity):
    """test eager pre-initialization."""
    pool = FixedPool(simple_object_class, capacity, pre_initialize=True)
    assert pool.available() == capacity


def test_fixed_pool_reset_method(simple_object_class, capacity):
    """test reset method is called."""
    pool = FixedPool(simple_object_class, capacity, reset_method="reset")

    obj = pool.get()
    obj.value = 42
    pool.release(obj)

    obj2 = pool.get()
    assert obj2.value == 0  # should be reset
    assert obj2.reset_called


def test_fixed_pool_double_release(simple_object_class, capacity):
    """test double release raises error."""
    pool = FixedPool(simple_object_class, capacity)

    obj = pool.get()
    pool.release(obj)

    with pytest.raises(AlreadyReleasedError):
        pool.release(obj)


def test_fixed_pool_wrong_type_release(simple_object_class, capacity):
    """test releasing wrong type raises error."""
    pool = FixedPool(simple_object_class, capacity)

    class OtherObject:
        pass

    with pytest.raises(TypeMismatchError):
        pool.release(OtherObject())


def test_fixed_pool_close(simple_object_class, capacity):
    """test closing pool."""
    pool = FixedPool(simple_object_class, capacity)
    pool.close()

    assert pool.is_closed()

    with pytest.raises(PoolClosedError):
        pool.get()


def test_fixed_pool_statistics(simple_object_class, capacity):
    """test statistics collection."""
    pool = FixedPool(simple_object_class, capacity, enable_statistics=True)

    obj = pool.get()
    pool.release(obj)

    stats = pool.stats().snapshot()
    assert stats["total_allocations"] == 1
    assert stats["total_releases"] == 1


def test_fixed_pool_custom_factory(capacity):
    """test custom factory function."""
    call_count = [0]

    def factory():
        call_count[0] += 1
        return object()

    pool = FixedPool(object, capacity, factory=factory)
    pool.get()

    assert call_count[0] == 1
