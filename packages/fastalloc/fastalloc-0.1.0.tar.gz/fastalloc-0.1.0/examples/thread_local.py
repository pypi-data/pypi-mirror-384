"""thread-local pool example."""

import threading
import time

from fastalloc import ThreadLocalPool


class ThreadData:
    """thread-specific data object."""

    def __init__(self):
        self.thread_id = threading.get_ident()
        self.operations = []

    def add_operation(self, op):
        """add operation to history."""
        self.operations.append(op)


def example_thread_local():
    """demonstrate thread-local pools."""
    print("=== Thread-Local Pool ===\n")

    # each thread gets its own pool
    pool = ThreadLocalPool(ThreadData, capacity=5)

    results = {}
    lock = threading.Lock()

    def worker(worker_id):
        """worker function."""
        # each thread uses its own pool instance
        obj = pool.get()
        obj.add_operation(f"worker_{worker_id}_started")

        time.sleep(0.01)  # simulate work

        obj.add_operation(f"worker_{worker_id}_finished")

        with lock:
            results[worker_id] = {
                "thread_id": threading.get_ident(),
                "operations": obj.operations.copy(),
            }

        pool.release(obj)

    # run multiple workers
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # verify each worker had isolated data
    print("Worker results:")
    for worker_id, data in results.items():
        print(f"  Worker {worker_id}: {len(data['operations'])} operations")

    # aggregate statistics
    stats = pool.stats().snapshot()
    print(f"\nAggregated statistics:")
    print(f"  Total allocations: {stats['total_allocations']}")
    print(f"  Total releases: {stats['total_releases']}\n")


if __name__ == "__main__":
    example_thread_local()
