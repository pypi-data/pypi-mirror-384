"""pytest benchmark configuration."""

import pytest


class BenchmarkObject:
    """object for benchmarking."""

    def __init__(self, value: int = 0) -> None:
        self.value = value
        self.data = [0] * 10

    def reset(self) -> None:
        """reset object."""
        self.value = 0
        self.data = [0] * 10


@pytest.fixture
def benchmark_object_class():
    """provide benchmark object class."""
    return BenchmarkObject
