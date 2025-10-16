"""unit tests for thread-safe pool."""

import concurrent.futures
import threading

import pytest

from fastalloc import ThreadSafePool


def test_thread_safe_pool_creation(simple_object_class, capacity):
    """test creating thread-safe pool."""
    pool = ThreadSafePool(simple_object_class, capacity)
    assert pool.capacity() == capacity


def test_thread_safe_pool_basic_operations(simple_object_class, capacity):
    """test basic get/release in single thread."""
    pool = ThreadSafePool(simple_object_class, capacity)

    obj = pool.get()
    assert isinstance(obj, simple_object_class)

    pool.release(obj)
    assert pool.available() == 1


def test_thread_safe_pool_concurrent_access(simple_object_class):
    """test concurrent access from multiple threads."""
    pool = ThreadSafePool(simple_object_class, capacity=100, pre_initialize=True)
    results = []
    errors = []

    def worker():
        try:
            for _ in range(10):
                obj = pool.get()
                obj.value = threading.get_ident()
                pool.release(obj)
            results.append(True)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    assert len(results) == 10
    assert pool.available() == 100


def test_thread_safe_pool_with_executor(simple_object_class):
    """test with thread pool executor."""
    pool = ThreadSafePool(simple_object_class, capacity=50)

    def task(i):
        obj = pool.get()
        obj.value = i
        pool.release(obj)
        return i

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(task, i) for i in range(100)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert len(results) == 100
