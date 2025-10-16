"""benchmark allocation speed."""

import pytest

from fastalloc import FixedPool


def test_benchmark_pool_allocation(benchmark, benchmark_object_class):
    """benchmark pool allocation speed."""
    pool = FixedPool(benchmark_object_class, capacity=1000, pre_initialize=True)

    def allocate_release():
        obj = pool.get()
        pool.release(obj)

    result = benchmark(allocate_release)
    print(f"\nPool allocation: {result.stats.mean * 1e9:.2f} ns/op")


def test_benchmark_naive_allocation(benchmark, benchmark_object_class):
    """benchmark naive object creation."""

    def create_object():
        obj = benchmark_object_class()
        # simulate some usage
        del obj

    result = benchmark(create_object)
    print(f"\nNaive allocation: {result.stats.mean * 1e9:.2f} ns/op")


def test_benchmark_pool_with_reset(benchmark, benchmark_object_class):
    """benchmark pool allocation with reset."""
    pool = FixedPool(
        benchmark_object_class,
        capacity=1000,
        pre_initialize=True,
        reset_method="reset",
    )

    def allocate_release_reset():
        obj = pool.get()
        obj.value = 42
        pool.release(obj)

    result = benchmark(allocate_release_reset)
    print(f"\nPool with reset: {result.stats.mean * 1e9:.2f} ns/op")


@pytest.mark.parametrize("capacity", [10, 100, 1000])
def test_benchmark_different_capacities(benchmark, benchmark_object_class, capacity):
    """benchmark with different pool capacities."""
    pool = FixedPool(benchmark_object_class, capacity=capacity, pre_initialize=True)

    def allocate_release():
        obj = pool.get()
        pool.release(obj)

    result = benchmark(allocate_release)
    print(f"\nCapacity {capacity}: {result.stats.mean * 1e9:.2f} ns/op")
