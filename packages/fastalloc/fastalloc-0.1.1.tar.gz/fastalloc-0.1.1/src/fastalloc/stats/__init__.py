"""statistics collection and reporting for fastalloc."""

from .collector import StatsCollector
from .reporter import StatsReporter

__all__ = [
    "StatsCollector",
    "StatsReporter",
]
