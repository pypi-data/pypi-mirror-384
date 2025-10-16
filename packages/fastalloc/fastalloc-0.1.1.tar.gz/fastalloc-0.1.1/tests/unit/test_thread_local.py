"""unit tests for thread-local pool."""

import threading

import pytest

from fastalloc import ThreadLocalPool


def test_thread_local_pool_creation(simple_object_class, capacity):
    """test creating thread-local pool."""
    pool = ThreadLocalPool(simple_object_class, capacity)
    assert pool.capacity() == capacity


def test_thread_local_pool_isolation(simple_object_class):
    """test pools are isolated per thread."""
    pool = ThreadLocalPool(simple_object_class, capacity=5)
    results = {}

    def worker(thread_id):
        obj1 = pool.get()
        obj1.value = thread_id
        obj2 = pool.get()
        obj2.value = thread_id + 100
        results[thread_id] = (id(obj1), id(obj2))
        pool.release(obj1)
        pool.release(obj2)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # verify different threads got different objects
    assert len(results) == 3
    all_ids = [id_pair for id_pair in results.values()]
    flat_ids = [item for pair in all_ids for item in pair]
    assert len(set(flat_ids)) == 6  # all unique


def test_thread_local_pool_statistics(simple_object_class):
    """test statistics aggregation."""
    pool = ThreadLocalPool(simple_object_class, capacity=5, enable_statistics=True)

    def worker():
        for _ in range(5):
            obj = pool.get()
            pool.release(obj)

    threads = [threading.Thread(target=worker) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    stats = pool.stats().snapshot()
    assert stats["total_allocations"] == 15  # 3 threads * 5 allocations
    assert stats["total_releases"] == 15
