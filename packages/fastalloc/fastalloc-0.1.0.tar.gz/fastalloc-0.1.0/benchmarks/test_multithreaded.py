"""multithreaded benchmarks."""

import threading

import pytest

from fastalloc import ThreadSafePool, ThreadLocalPool


class ThreadWorkObject:
    """object for threaded benchmarks."""

    def __init__(self):
        self.value = 0


def test_benchmark_thread_safe_pool(benchmark):
    """benchmark thread-safe pool with contention."""
    pool = ThreadSafePool(ThreadWorkObject, capacity=100, pre_initialize=True)

    def threaded_work():
        def worker():
            for _ in range(100):
                obj = pool.get()
                obj.value += 1
                pool.release(obj)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    result = benchmark(threaded_work)
    print(f"\nThread-safe pool: {result.stats.mean * 1e3:.2f} ms")


def test_benchmark_thread_local_pool(benchmark):
    """benchmark thread-local pool."""
    pool = ThreadLocalPool(ThreadWorkObject, capacity=20)

    def threaded_work():
        def worker():
            for _ in range(100):
                obj = pool.get()
                obj.value += 1
                pool.release(obj)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    result = benchmark(threaded_work)
    print(f"\nThread-local pool: {result.stats.mean * 1e3:.2f} ms")
