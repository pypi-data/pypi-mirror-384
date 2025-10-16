"""basic usage examples."""

from fastalloc import Pool


class DataObject:
    """simple data object."""

    def __init__(self):
        self.data = []
        self.processed = False

    def reset(self):
        """reset object state."""
        self.data = []
        self.processed = False


def example_basic():
    """basic pool usage."""
    print("=== Basic Usage ===\n")

    # create a pool
    pool = Pool(DataObject, capacity=10)

    # get an object
    obj = pool.get()
    obj.data = [1, 2, 3]
    print(f"Object data: {obj.data}")

    # return it
    pool.release(obj)
    print("Object released\n")


def example_context_manager():
    """using context manager."""
    print("=== Context Manager ===\n")

    pool = Pool(DataObject, capacity=10)

    # automatically releases on exit
    with pool.allocate() as obj:
        obj.data = [4, 5, 6]
        print(f"Object data: {obj.data}")

    print("Object auto-released\n")


def example_with_reset():
    """using reset method."""
    print("=== With Reset Method ===\n")

    pool = Pool(DataObject, capacity=10, reset_method="reset")

    obj = pool.get()
    obj.data = [7, 8, 9]
    obj.processed = True
    print(f"Before release: data={obj.data}, processed={obj.processed}")

    pool.release(obj)

    obj2 = pool.get()
    print(f"After get: data={obj2.data}, processed={obj2.processed}")
    print("Object was reset!\n")

    pool.release(obj2)


def example_statistics():
    """collecting statistics."""
    print("=== Statistics ===\n")

    pool = Pool(DataObject, capacity=10, enable_statistics=True)

    # perform some operations
    objs = [pool.get() for _ in range(5)]
    for obj in objs:
        pool.release(obj)

    # view statistics
    stats = pool.stats().snapshot()
    print(f"Total allocations: {stats['total_allocations']}")
    print(f"Total releases: {stats['total_releases']}")
    print(f"Peak in use: {stats['peak_in_use']}\n")


if __name__ == "__main__":
    example_basic()
    example_context_manager()
    example_with_reset()
    example_statistics()
