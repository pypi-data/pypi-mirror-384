"""property-based tests using hypothesis."""

from hypothesis import given, strategies as st

from fastalloc import FixedPool


class SimpleObject:
    def __init__(self):
        self.value = 0


@given(st.integers(min_value=1, max_value=100))
def test_pool_capacity_property(capacity):
    """test pool capacity property holds."""
    pool = FixedPool(SimpleObject, capacity=capacity)
    assert pool.capacity() == capacity


@given(st.integers(min_value=1, max_value=50))
def test_pool_size_invariant(capacity):
    """test in_use + available <= capacity."""
    pool = FixedPool(SimpleObject, capacity=capacity)

    objs = []
    for _ in range(capacity // 2):
        objs.append(pool.get())

    # in_use + available should equal total allocated
    assert pool.size() + pool.available() <= capacity

    for obj in objs:
        pool.release(obj)

    assert pool.size() == 0
