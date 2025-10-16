"""async usage example."""

import asyncio

from fastalloc import AsyncPool


class AsyncConnection:
    """async connection object."""

    def __init__(self):
        self.data = []
        self.connected = False

    async def connect(self):
        """simulate async connection."""
        await asyncio.sleep(0.01)
        self.connected = True

    async def fetch_data(self):
        """simulate async data fetch."""
        await asyncio.sleep(0.01)
        self.data.append("fetched")

    def reset(self):
        """reset connection."""
        self.data = []
        self.connected = False


async def example_async_basic():
    """basic async pool usage."""
    print("=== Async Basic Usage ===\n")

    pool = AsyncPool(AsyncConnection, capacity=10, reset_method="reset")

    # use async context manager
    async with pool.allocate() as conn:
        await conn.connect()
        await conn.fetch_data()
        print(f"Connected: {conn.connected}")
        print(f"Data: {conn.data}\n")


async def example_async_concurrent():
    """concurrent async operations."""
    print("=== Async Concurrent ===\n")

    pool = AsyncPool(AsyncConnection, capacity=20, pre_initialize=True)

    async def task(task_id):
        async with pool.allocate() as conn:
            await conn.connect()
            await conn.fetch_data()
            return task_id

    # run 50 concurrent tasks with pool of 20
    results = await asyncio.gather(*[task(i) for i in range(50)])

    print(f"Completed {len(results)} tasks")
    print(f"Pool capacity: {pool.capacity()}")
    print(f"Available: {pool.available()}\n")


async def main():
    """run all async examples."""
    await example_async_basic()
    await example_async_concurrent()


if __name__ == "__main__":
    asyncio.run(main())
