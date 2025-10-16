"""unit tests for decorators."""

import pytest

from fastalloc import GrowthStrategy, pooled


def test_pooled_decorator_basic():
    """test basic pooled decorator."""

    @pooled(capacity=10)
    class TestObject:
        def __init__(self):
            self.value = 0

    assert hasattr(TestObject, "pool")
    assert TestObject.pool.capacity() == 10


def test_pooled_decorator_usage():
    """test using pooled decorator."""

    @pooled(capacity=5)
    class Worker:
        def __init__(self):
            self.data = []

        def process(self, item):
            self.data.append(item)

    with Worker.pool.allocate() as worker:
        worker.process(42)
        assert 42 in worker.data


def test_pooled_decorator_thread_safe():
    """test pooled decorator with thread_safe."""

    @pooled(capacity=10, thread_safe=True)
    class ThreadSafeObject:
        pass

    from fastalloc.pool import ThreadSafePool

    assert isinstance(ThreadSafeObject.pool, ThreadSafePool)


def test_pooled_decorator_thread_local():
    """test pooled decorator with thread_local."""

    @pooled(capacity=10, thread_local=True)
    class ThreadLocalObject:
        pass

    from fastalloc.pool import ThreadLocalPool

    assert isinstance(ThreadLocalObject.pool, ThreadLocalPool)


def test_pooled_decorator_with_reset():
    """test pooled decorator with reset method."""

    @pooled(capacity=5, reset_method="reset")
    class ResettableObject:
        def __init__(self):
            self.value = 0

        def reset(self):
            self.value = 0

    obj = ResettableObject.pool.get()
    obj.value = 99
    ResettableObject.pool.release(obj)

    obj2 = ResettableObject.pool.get()
    assert obj2.value == 0


def test_pooled_decorator_invalid_config():
    """test pooled decorator rejects invalid config."""

    with pytest.raises(ValueError):

        @pooled(capacity=10, thread_safe=True, thread_local=True)
        class InvalidObject:
            pass
