"""unit tests for growing pool."""

import pytest

from fastalloc import GrowingPool, PoolEmptyError
from fastalloc.config import GrowthStrategy, linear_growth, exponential_growth


def test_growing_pool_linear_growth(simple_object_class):
    """test linear growth strategy."""
    growth_config = linear_growth(increment=5, max_capacity=20)
    pool = GrowingPool(simple_object_class, capacity=5, growth_config=growth_config)

    # exhaust initial capacity
    objs = [pool.get() for _ in range(5)]
    assert pool.capacity() == 5

    # trigger growth
    obj6 = pool.get()
    assert pool.capacity() == 10

    # release and verify
    for obj in objs:
        pool.release(obj)
    pool.release(obj6)


def test_growing_pool_exponential_growth(simple_object_class):
    """test exponential growth strategy."""
    growth_config = exponential_growth(factor=2.0, max_capacity=100)
    pool = GrowingPool(simple_object_class, capacity=5, growth_config=growth_config)

    # exhaust initial capacity
    objs = [pool.get() for _ in range(5)]
    assert pool.capacity() == 5

    # trigger growth
    obj6 = pool.get()
    assert pool.capacity() == 10  # 5 * 2.0

    for obj in objs + [obj6]:
        pool.release(obj)


def test_growing_pool_max_capacity(simple_object_class):
    """test max capacity limit."""
    growth_config = linear_growth(increment=5, max_capacity=10)
    pool = GrowingPool(simple_object_class, capacity=5, growth_config=growth_config)

    # exhaust and grow to max
    objs = [pool.get() for _ in range(10)]
    assert pool.capacity() == 10

    # try to exceed max capacity
    with pytest.raises(PoolEmptyError):
        pool.get()

    for obj in objs:
        pool.release(obj)


def test_growing_pool_default_config(simple_object_class):
    """test default growth configuration."""
    pool = GrowingPool(simple_object_class, capacity=10, max_capacity=50)

    # should use default linear growth
    objs = [pool.get() for _ in range(10)]
    obj11 = pool.get()  # trigger growth

    assert pool.capacity() > 10

    for obj in objs + [obj11]:
        pool.release(obj)


def test_growing_pool_pre_initialize(simple_object_class):
    """test pre-initialization with growing pool."""
    pool = GrowingPool(simple_object_class, capacity=5, pre_initialize=True)
    assert pool.available() == 5
