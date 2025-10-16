"""statistics reporting and formatting."""

from typing import Dict

from .collector import StatsCollector


class StatsReporter:
    # purpose: formats statistics from collector into nice human-readable text.
    # params: collector - the StatsCollector to report on.
    # args: collector required.
    # returns: n/a - initializer.
    # raises: none.
    """formats and reports pool statistics."""

    # purpose: sets up reporter with a stats collector.
    # params: self, collector - StatsCollector to use.
    # args: collector required.
    # returns: n/a - initializer.
    # raises: none.
    def __init__(self, collector: StatsCollector) -> None:
        self.collector = collector

    # purpose: creates a dictionary with all stats in structured format.
    # params: self.
    # args: none.
    # returns: dictionary with all statistics.
    # raises: none.
    def to_dict(self) -> Dict[str, int]:
        """get statistics as dictionary."""
        return self.collector.snapshot()

    # purpose: formats statistics as a nice text report with lines for each stat.
    # params: self.
    # args: none.
    # returns: multi-line string with formatted stats.
    # raises: none.
    def to_text(self) -> str:
        """format statistics as text report."""
        stats = self.collector.snapshot()

        lines = [
            "pool statistics",
            "=" * 50,
            "",
            "allocations:",
            f"  total: {stats['total_allocations']:,}",
            f"  average time: {stats['avg_allocation_time_ns']:,} ns",
            "",
            "releases:",
            f"  total: {stats['total_releases']:,}",
            f"  average time: {stats['avg_release_time_ns']:,} ns",
            "",
            "resets:",
            f"  total: {stats['total_resets']:,}",
            "",
            "capacity:",
            f"  current: {stats['current_capacity']:,}",
            f"  peak: {stats['peak_capacity']:,}",
            f"  growth events: {stats['growth_events']:,}",
            "",
            "usage:",
            f"  current in use: {stats['current_in_use']:,}",
            f"  peak in use: {stats['peak_in_use']:,}",
            "",
        ]

        return "\n".join(lines)

    # purpose: prints the text report to console.
    # params: self.
    # args: none.
    # returns: nothing.
    # raises: none.
    def print_report(self) -> None:
        """print statistics report."""
        print(self.to_text())

    # purpose: creates a compact one-line summary of key stats.
    # params: self.
    # args: none.
    # returns: short string with main statistics.
    # raises: none.
    def summary(self) -> str:
        """get one-line summary of statistics."""
        stats = self.collector.snapshot()
        return (
            f"allocs={stats['total_allocations']:,} "
            f"releases={stats['total_releases']:,} "
            f"in_use={stats['current_in_use']:,}/{stats['current_capacity']:,} "
            f"peak={stats['peak_in_use']:,}"
        )
