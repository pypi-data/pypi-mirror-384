"""statistics and monitoring examples."""

from fastalloc import Pool
from fastalloc.stats import StatsReporter


class MonitoredObject:
    """object to monitor."""

    def __init__(self):
        self.value = 0

    def reset(self):
        """reset object."""
        self.value = 0


def example_statistics_collection():
    """demonstrate statistics collection."""
    print("=== Statistics Collection ===\n")

    pool = Pool(
        MonitoredObject,
        capacity=20,
        enable_statistics=True,
        reset_method="reset",
    )

    # perform various operations
    objs = []
    for i in range(10):
        obj = pool.get()
        obj.value = i
        objs.append(obj)

    # release half
    for obj in objs[:5]:
        pool.release(obj)

    # get statistics snapshot
    stats = pool.stats().snapshot()

    print("Current Statistics:")
    print(f"  Total allocations: {stats['total_allocations']}")
    print(f"  Total releases: {stats['total_releases']}")
    print(f"  Total resets: {stats['total_resets']}")
    print(f"  Current in use: {stats['current_in_use']}")
    print(f"  Peak in use: {stats['peak_in_use']}")
    print(f"  Current capacity: {stats['current_capacity']}")

    if stats["total_allocations"] > 0:
        print(f"  Avg allocation time: {stats['avg_allocation_time_ns']} ns")
    if stats["total_releases"] > 0:
        print(f"  Avg release time: {stats['avg_release_time_ns']} ns")

    # cleanup
    for obj in objs[5:]:
        pool.release(obj)

    print()


def example_statistics_reporting():
    """demonstrate statistics reporting."""
    print("=== Statistics Reporting ===\n")

    pool = Pool(
        MonitoredObject,
        capacity=15,
        enable_statistics=True,
    )

    # do some work
    for _ in range(25):
        obj = pool.get()
        pool.release(obj)

    # create reporter
    reporter = StatsReporter(pool.stats())

    # get formatted report
    print(reporter.to_text())

    # get summary
    print(f"Summary: {reporter.summary()}\n")


def example_monitoring_loop():
    """demonstrate continuous monitoring."""
    print("=== Monitoring Loop ===\n")

    pool = Pool(
        MonitoredObject,
        capacity=10,
        enable_statistics=True,
    )

    print("Performing work...")
    for i in range(5):
        # do batch of work
        objs = [pool.get() for _ in range(5)]
        for obj in objs:
            pool.release(obj)

        # check current state
        stats = pool.stats().snapshot()
        print(f"Iteration {i + 1}: "
              f"allocs={stats['total_allocations']}, "
              f"in_use={stats['current_in_use']}")

    print()


if __name__ == "__main__":
    example_statistics_collection()
    example_statistics_reporting()
    example_monitoring_loop()
