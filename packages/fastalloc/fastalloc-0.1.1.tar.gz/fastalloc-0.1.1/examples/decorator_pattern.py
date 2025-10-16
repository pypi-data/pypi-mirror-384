"""decorator pattern example."""

from fastalloc import pooled


@pooled(capacity=100, thread_safe=True, enable_statistics=True)
class Worker:
    """worker object with attached pool."""

    def __init__(self):
        self.tasks_completed = 0
        self.results = []

    def reset(self):
        """reset worker state."""
        self.tasks_completed = 0
        self.results = []

    def process(self, data):
        """process some data."""
        result = sum(data) if data else 0
        self.results.append(result)
        self.tasks_completed += 1
        return result


def example_decorator():
    """demonstrate decorator usage."""
    print("=== Decorator Pattern ===\n")

    # pool is automatically attached to class
    print(f"Worker pool capacity: {Worker.pool.capacity()}")

    # use the pool
    with Worker.pool.allocate() as worker:
        result = worker.process([1, 2, 3, 4, 5])
        print(f"Processing result: {result}")
        print(f"Tasks completed: {worker.tasks_completed}")

    # check statistics
    stats = Worker.pool.stats().snapshot()
    print(f"\nPool statistics:")
    print(f"  Total allocations: {stats['total_allocations']}")
    print(f"  Total releases: {stats['total_releases']}\n")


@pooled(capacity=50, reset_method="reset")
class Connection:
    """connection object with auto-reset."""

    def __init__(self):
        self.connected = False
        self.data_received = []

    def reset(self):
        """reset connection state."""
        self.connected = False
        self.data_received = []

    def connect(self):
        """establish connection."""
        self.connected = True

    def receive(self, data):
        """receive data."""
        if self.connected:
            self.data_received.append(data)


def example_with_reset_decorator():
    """demonstrate decorator with reset."""
    print("=== Decorator with Reset ===\n")

    # first usage
    with Connection.pool.allocate() as conn:
        conn.connect()
        conn.receive("data1")
        print(f"First usage - received: {conn.data_received}")

    # second usage - should be reset
    with Connection.pool.allocate() as conn:
        print(f"Second usage - received: {conn.data_received}")
        print("Connection was reset!\n")


if __name__ == "__main__":
    example_decorator()
    example_with_reset_decorator()
