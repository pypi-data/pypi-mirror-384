"""statistics collection for pools."""

import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Dict, Optional


@dataclass
class StatsCollector:
    # purpose: collects and tracks various statistics about pool usage.
    # params: enabled - whether to collect stats.
    # args: enabled optional, defaults to true.
    # returns: n/a - dataclass.
    # raises: none.
    """collects statistics about pool operations."""

    enabled: bool = True

    # counters
    total_allocations: int = field(default=0, init=False)
    total_releases: int = field(default=0, init=False)
    total_resets: int = field(default=0, init=False)
    growth_events: int = field(default=0, init=False)

    # peaks
    peak_in_use: int = field(default=0, init=False)
    peak_capacity: int = field(default=0, init=False)

    # current state
    current_in_use: int = field(default=0, init=False)
    current_capacity: int = field(default=0, init=False)

    # timing (nanoseconds)
    total_allocation_time_ns: int = field(default=0, init=False)
    total_release_time_ns: int = field(default=0, init=False)

    # lock for thread safety
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)

    # purpose: records that an allocation happened.
    # params: self, duration_ns - optional time it took in nanoseconds.
    # args: duration_ns optional.
    # returns: nothing.
    # raises: none.
    def record_allocation(self, duration_ns: Optional[int] = None) -> None:
        """record an allocation event."""
        with self._lock:
            # always track current_in_use for size() method
            self.current_in_use += 1

            if not self.enabled:
                return

            self.total_allocations += 1
            if self.current_in_use > self.peak_in_use:
                self.peak_in_use = self.current_in_use
            if duration_ns is not None:
                self.total_allocation_time_ns += duration_ns

    # purpose: records that an object was released back to pool.
    # params: self, duration_ns - optional time it took.
    # args: duration_ns optional.
    # returns: nothing.
    # raises: none.
    def record_release(self, duration_ns: Optional[int] = None) -> None:
        """record a release event."""
        with self._lock:
            # always track current_in_use for size() method
            self.current_in_use = max(0, self.current_in_use - 1)

            if not self.enabled:
                return

            self.total_releases += 1
            if duration_ns is not None:
                self.total_release_time_ns += duration_ns

    # purpose: records that an object was reset.
    # params: self.
    # args: none.
    # returns: nothing.
    # raises: none.
    def record_reset(self) -> None:
        """record a reset event."""
        if not self.enabled:
            return

        with self._lock:
            self.total_resets += 1

    # purpose: records that the pool grew in size.
    # params: self, new_capacity - what the capacity is now.
    # args: new_capacity required.
    # returns: nothing.
    # raises: none.
    def record_growth(self, new_capacity: int) -> None:
        """record a pool growth event."""
        if not self.enabled:
            return

        with self._lock:
            self.growth_events += 1
            self.current_capacity = new_capacity
            if new_capacity > self.peak_capacity:
                self.peak_capacity = new_capacity

    # purpose: updates the current capacity tracker.
    # params: self, capacity - new capacity value.
    # args: capacity required.
    # returns: nothing.
    # raises: none.
    def update_capacity(self, capacity: int) -> None:
        """update current capacity."""
        if not self.enabled:
            return

        with self._lock:
            self.current_capacity = capacity
            if capacity > self.peak_capacity:
                self.peak_capacity = capacity

    # purpose: gets a copy of all statistics as a dictionary.
    # params: self.
    # args: none.
    # returns: dictionary with all stats.
    # raises: none.
    def snapshot(self) -> Dict[str, int]:
        """get snapshot of current statistics."""
        with self._lock:
            return {
                "total_allocations": self.total_allocations,
                "total_releases": self.total_releases,
                "total_resets": self.total_resets,
                "growth_events": self.growth_events,
                "peak_in_use": self.peak_in_use,
                "peak_capacity": self.peak_capacity,
                "current_in_use": self.current_in_use,
                "current_capacity": self.current_capacity,
                "total_allocation_time_ns": self.total_allocation_time_ns,
                "total_release_time_ns": self.total_release_time_ns,
                "avg_allocation_time_ns": (
                    self.total_allocation_time_ns // self.total_allocations
                    if self.total_allocations > 0
                    else 0
                ),
                "avg_release_time_ns": (
                    self.total_release_time_ns // self.total_releases
                    if self.total_releases > 0
                    else 0
                ),
            }

    # purpose: combines stats from another collector into this one.
    # params: self, other - another StatsCollector to merge.
    # args: other required.
    # returns: nothing.
    # raises: none.
    def merge(self, other: "StatsCollector") -> None:
        """merge statistics from another collector."""
        if not self.enabled:
            return

        other_snapshot = other.snapshot()
        with self._lock:
            self.total_allocations += other_snapshot["total_allocations"]
            self.total_releases += other_snapshot["total_releases"]
            self.total_resets += other_snapshot["total_resets"]
            self.growth_events += other_snapshot["growth_events"]
            self.peak_in_use = max(self.peak_in_use, other_snapshot["peak_in_use"])
            self.peak_capacity = max(self.peak_capacity, other_snapshot["peak_capacity"])
            self.total_allocation_time_ns += other_snapshot["total_allocation_time_ns"]
            self.total_release_time_ns += other_snapshot["total_release_time_ns"]

    # purpose: resets all statistics back to zero.
    # params: self.
    # args: none.
    # returns: nothing.
    # raises: none.
    def reset(self) -> None:
        """reset all statistics to zero."""
        with self._lock:
            self.total_allocations = 0
            self.total_releases = 0
            self.total_resets = 0
            self.growth_events = 0
            self.peak_in_use = 0
            self.peak_capacity = 0
            self.current_in_use = 0
            self.current_capacity = 0
            self.total_allocation_time_ns = 0
            self.total_release_time_ns = 0


# purpose: helper to measure how long an operation takes.
# params: none.
# args: none.
# returns: current time in nanoseconds.
# raises: none.
def now_ns() -> int:
    """get current time in nanoseconds."""
    return time.perf_counter_ns()
