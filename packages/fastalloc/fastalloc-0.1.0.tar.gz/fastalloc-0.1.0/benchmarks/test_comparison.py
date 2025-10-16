"""comparison benchmarks between pool and naive allocation."""

import gc

import pytest

from fastalloc import FixedPool


class WorkObject:
    """realistic work object."""

    def __init__(self):
        self.data = list(range(100))
        self.state = {"key": "value"}
        self.counter = 0

    def reset(self):
        """reset object state."""
        self.data = list(range(100))
        self.state = {"key": "value"}
        self.counter = 0

    def do_work(self):
        """simulate work."""
        self.counter += 1
        self.state["result"] = sum(self.data)


def test_benchmark_pool_vs_naive_simple(benchmark):
    """compare simple pool vs naive for many iterations."""
    pool = FixedPool(WorkObject, capacity=10, pre_initialize=True, reset_method="reset")

    def with_pool():
        for _ in range(100):
            obj = pool.get()
            obj.do_work()
            pool.release(obj)

    result = benchmark(with_pool)
    print(f"\nPool (100 iterations): {result.stats.mean * 1e6:.2f} µs")


def test_benchmark_naive_creation(benchmark):
    """benchmark naive object creation for comparison."""

    def naive():
        for _ in range(100):
            obj = WorkObject()
            obj.do_work()
            del obj

    result = benchmark(naive)
    print(f"\nNaive (100 iterations): {result.stats.mean * 1e6:.2f} µs")


def test_benchmark_gc_pressure_pool(benchmark):
    """measure GC pressure with pool."""
    pool = FixedPool(WorkObject, capacity=100, pre_initialize=True)

    def with_pool():
        gc_count_before = gc.get_count()
        for _ in range(1000):
            obj = pool.get()
            obj.do_work()
            pool.release(obj)
        gc_count_after = gc.get_count()
        return gc_count_after[0] - gc_count_before[0]

    result = benchmark(with_pool)
    print(f"\nGC pressure (pool): {result.stats.mean:.2f} collections")


def test_benchmark_gc_pressure_naive(benchmark):
    """measure GC pressure with naive allocation."""

    def naive():
        gc_count_before = gc.get_count()
        for _ in range(1000):
            obj = WorkObject()
            obj.do_work()
            del obj
        gc_count_after = gc.get_count()
        return gc_count_after[0] - gc_count_before[0]

    result = benchmark(naive)
    print(f"\nGC pressure (naive): {result.stats.mean:.2f} collections")
