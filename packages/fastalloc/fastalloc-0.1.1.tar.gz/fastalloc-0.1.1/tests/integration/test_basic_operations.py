"""integration tests for basic pool operations."""

import pytest

from fastalloc import FixedPool, GrowingPool, ThreadSafePool


def test_pool_lifecycle(simple_object_class):
    """test complete pool lifecycle."""
    pool = FixedPool(simple_object_class, capacity=10, enable_statistics=True)

    # allocate multiple objects
    objs = [pool.get() for _ in range(5)]
    assert pool.size() == 5

    # use objects
    for i, obj in enumerate(objs):
        obj.value = i

    # release objects
    for obj in objs:
        pool.release(obj)

    assert pool.size() == 0
    assert pool.available() == 5

    # verify stats
    stats = pool.stats().snapshot()
    assert stats["total_allocations"] == 5
    assert stats["total_releases"] == 5


def test_mixed_pool_types(simple_object_class):
    """test using different pool types together."""
    fixed = FixedPool(simple_object_class, capacity=10)
    growing = GrowingPool(simple_object_class, capacity=10, max_capacity=50)
    thread_safe = ThreadSafePool(simple_object_class, capacity=10)

    obj1 = fixed.get()
    obj2 = growing.get()
    obj3 = thread_safe.get()

    fixed.release(obj1)
    growing.release(obj2)
    thread_safe.release(obj3)


def test_context_manager_with_exception(simple_object_class):
    """test context manager releases on exception."""
    pool = FixedPool(simple_object_class, capacity=5)

    try:
        with pool.allocate() as obj:
            obj.value = 42
            raise ValueError("test error")
    except ValueError:
        pass

    # object should be released despite exception
    assert pool.available() == 1


def test_builder_to_usage_flow(simple_object_class):
    """test complete flow from builder to usage."""
    from fastalloc import GrowthStrategy, PoolBuilder

    pool = (
        PoolBuilder()
        .type(simple_object_class)
        .capacity(5)
        .max_capacity(20)
        .growth_strategy(GrowthStrategy.LINEAR, increment=5)
        .enable_statistics(True)
        .reset_method("reset")
        .build()
    )

    # exhaust and grow
    objs = []
    for i in range(10):
        obj = pool.get()
        obj.value = i
        objs.append(obj)

    assert pool.capacity() == 10  # should have grown

    # release all
    for obj in objs:
        pool.release(obj)

    # verify reset was called
    stats = pool.stats().snapshot()
    assert stats["total_resets"] > 0
