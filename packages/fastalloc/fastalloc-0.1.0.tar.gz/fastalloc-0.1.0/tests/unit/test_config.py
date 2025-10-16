"""unit tests for configuration."""

import pytest

from fastalloc import PoolBuilder, PoolConfigurationError
from fastalloc.config import GrowthStrategy, linear_growth, exponential_growth


def test_builder_basic(simple_object_class):
    """test basic builder usage."""
    pool = (
        PoolBuilder()
        .type(simple_object_class)
        .capacity(10)
        .build()
    )

    assert pool.capacity() == 10


def test_builder_with_growth(simple_object_class):
    """test builder with growth strategy."""
    pool = (
        PoolBuilder()
        .type(simple_object_class)
        .capacity(10)
        .max_capacity(100)
        .growth_strategy(GrowthStrategy.LINEAR, increment=10)
        .build()
    )

    assert pool.capacity() == 10


def test_builder_thread_safe(simple_object_class):
    """test builder creates thread-safe pool."""
    pool = (
        PoolBuilder()
        .type(simple_object_class)
        .capacity(10)
        .thread_safe(True)
        .build()
    )

    from fastalloc.pool import ThreadSafePool
    assert isinstance(pool, ThreadSafePool)


def test_builder_thread_local(simple_object_class):
    """test builder creates thread-local pool."""
    pool = (
        PoolBuilder()
        .type(simple_object_class)
        .capacity(10)
        .thread_local(True)
        .build()
    )

    from fastalloc.pool import ThreadLocalPool
    assert isinstance(pool, ThreadLocalPool)


def test_builder_missing_type():
    """test builder raises error without type."""
    with pytest.raises(PoolConfigurationError):
        PoolBuilder().capacity(10).build()


def test_builder_missing_capacity(simple_object_class):
    """test builder raises error without capacity."""
    with pytest.raises(PoolConfigurationError):
        PoolBuilder().type(simple_object_class).build()


def test_builder_thread_safe_and_local_conflict(simple_object_class):
    """test builder rejects both thread_safe and thread_local."""
    with pytest.raises(PoolConfigurationError):
        (
            PoolBuilder()
            .type(simple_object_class)
            .capacity(10)
            .thread_safe(True)
            .thread_local(True)
            .build()
        )


def test_linear_growth_config():
    """test linear growth configuration."""
    config = linear_growth(increment=10, max_capacity=100)

    assert config.calculate_new_capacity(50) == 60
    assert config.can_grow(50)
    assert not config.can_grow(100)


def test_exponential_growth_config():
    """test exponential growth configuration."""
    config = exponential_growth(factor=2.0, max_capacity=100)

    assert config.calculate_new_capacity(10) == 20
    assert config.calculate_new_capacity(50) == 100  # clamped to max
    assert config.can_grow(50)
    assert not config.can_grow(100)


def test_growth_invalid_increment():
    """test linear growth rejects invalid increment."""
    with pytest.raises(ValueError):
        linear_growth(increment=0)


def test_growth_invalid_factor():
    """test exponential growth rejects invalid factor."""
    with pytest.raises(ValueError):
        exponential_growth(factor=1.0)
