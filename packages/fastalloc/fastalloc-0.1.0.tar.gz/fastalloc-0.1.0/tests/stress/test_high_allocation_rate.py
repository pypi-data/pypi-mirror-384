"""stress test for high allocation rates."""

import pytest

from fastalloc import FixedPool, ThreadSafePool


@pytest.mark.slow
def test_high_allocation_rate(simple_object_class):
    """test pool under high allocation rate."""
    pool = FixedPool(simple_object_class, capacity=1000, pre_initialize=True)

    for _ in range(100000):
        obj = pool.get()
        obj.value = 42
        pool.release(obj)

    assert pool.available() == 1000


@pytest.mark.slow
def test_thread_safe_high_contention(simple_object_class):
    """test thread-safe pool under high contention."""
    import threading

    pool = ThreadSafePool(simple_object_class, capacity=100, pre_initialize=True)
    iterations = 1000
    errors = []

    def worker():
        try:
            for _ in range(iterations):
                obj = pool.get()
                pool.release(obj)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    assert pool.available() == 100
