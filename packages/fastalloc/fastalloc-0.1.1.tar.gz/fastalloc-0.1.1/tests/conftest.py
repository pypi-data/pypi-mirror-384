"""pytest configuration and fixtures."""

import pytest


class SimpleObject:
    """simple test object."""

    def __init__(self, value: int = 0) -> None:
        self.value = value
        self.reset_called = False

    def reset(self) -> None:
        """reset object state."""
        self.value = 0
        self.reset_called = True


class ObjectWithSlots:
    """test object using __slots__."""

    __slots__ = ["value", "reset_called"]

    def __init__(self, value: int = 0) -> None:
        self.value = value
        self.reset_called = False

    def reset(self) -> None:
        """reset object state."""
        self.value = 0
        self.reset_called = True


@pytest.fixture
def simple_object_class():
    """provide simple object class for tests."""
    return SimpleObject


@pytest.fixture
def slots_object_class():
    """provide slots object class for tests."""
    return ObjectWithSlots


@pytest.fixture
def capacity():
    """default capacity for tests."""
    return 10
