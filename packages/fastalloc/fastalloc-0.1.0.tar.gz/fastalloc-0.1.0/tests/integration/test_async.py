"""integration tests for async pool."""

import asyncio

import pytest

from fastalloc import AsyncPool


@pytest.mark.asyncio
async def test_async_pool_basic(simple_object_class):
    """test basic async pool operations."""
    pool = AsyncPool(simple_object_class, capacity=10)

    obj = await pool.get_async()
    assert isinstance(obj, simple_object_class)

    await pool.release_async(obj)
    assert pool.available() == 1


@pytest.mark.asyncio
async def test_async_pool_context_manager(simple_object_class):
    """test async context manager."""
    pool = AsyncPool(simple_object_class, capacity=10)

    async with pool.allocate() as obj:
        obj.value = 42
        assert obj.value == 42

    assert pool.available() == 1


@pytest.mark.asyncio
async def test_async_pool_concurrent_tasks(simple_object_class):
    """test concurrent async tasks."""
    pool = AsyncPool(simple_object_class, capacity=50, pre_initialize=True)

    async def task(task_id):
        obj = await pool.get_async()
        obj.value = task_id
        await asyncio.sleep(0.001)  # simulate work
        await pool.release_async(obj)
        return task_id

    results = await asyncio.gather(*[task(i) for i in range(50)])

    assert len(results) == 50
    assert pool.available() == 50
