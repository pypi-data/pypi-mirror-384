# Performance Guide

## Performance Targets

fastalloc achieves the following performance characteristics:

- **Object Acquisition**: < 50ns per object (fixed pool, pre-initialized)
- **Object Release**: < 30ns per object
- **GC Reduction**: 80%+ fewer collection cycles
- **Memory Overhead**: < 10% for pools over 1000 objects
- **Thread-Safe Pool**: < 200ns with moderate contention

## Optimization Techniques

### 1. Pre-Initialization

Create all objects upfront to eliminate lazy allocation overhead:

```python
pool = Pool(MyObject, capacity=1000, pre_initialize=True)
```

**Benefits:**
- No allocation overhead on first `get()`
- Predictable startup time
- Consistent performance

**Trade-offs:**
- Higher initial memory usage
- Longer pool creation time

### 2. Reset Methods

Reuse objects without reallocating:

```python
class MyObject:
    def reset(self):
        self.state = None
        self.data = []

pool = Pool(MyObject, capacity=1000, reset_method='reset')
```

**Benefits:**
- Avoids constructor overhead
- Maintains object identity
- Reduces GC pressure

### 3. Thread-Local Pools

Eliminate lock contention in multi-threaded applications:

```python
pool = ThreadLocalPool(MyObject, capacity=100)
```

**Benefits:**
- No locking overhead
- True parallel access
- Better cache locality

**Trade-offs:**
- Higher total memory usage (capacity × threads)
- Statistics aggregation overhead

### 4. Capacity Planning

Choose appropriate initial and maximum capacities:

```python
# For known workloads
pool = FixedPool(MyObject, capacity=exact_needed)

# For variable workloads
pool = GrowingPool(
    MyObject,
    capacity=typical_load,
    max_capacity=peak_load,
    growth_config=linear_growth(increment=100)
)
```

### 5. Growth Strategies

Choose the right growth strategy:

**Linear Growth:**
- Predictable memory usage
- Good for steady load increases
- Lower memory spikes

```python
growth_config = linear_growth(increment=100)
```

**Exponential Growth:**
- Faster capacity expansion
- Good for bursty workloads
- May overshoot actual need

```python
growth_config = exponential_growth(factor=2.0)
```

## Benchmarking

Use the included benchmarks to measure performance:

```bash
pytest benchmarks/ --benchmark-only
```

Compare with naive allocation:

```python
# Pool version
with pool.allocate() as obj:
    obj.process()

# Naive version
obj = MyObject()
obj.process()
del obj
```

## Profiling

Enable statistics to identify bottlenecks:

```python
pool = Pool(MyObject, capacity=1000, enable_statistics=True)

# ... use pool ...

stats = pool.stats().snapshot()
print(f"Avg allocation time: {stats['avg_allocation_time_ns']} ns")
```

## Best Practices

1. **Match capacity to workload**: Measure your actual usage patterns
2. **Pre-initialize for hot paths**: Eliminate allocation overhead where it matters
3. **Use reset methods**: Clean state without deallocating
4. **Choose appropriate pool type**: Match thread safety to your needs
5. **Monitor statistics**: Use stats to validate optimization decisions
6. **Benchmark regularly**: Verify performance improvements

## Common Pitfalls

1. **Over-allocation**: Don't create huge pools if you don't need them
2. **Ignoring reset**: Objects with state need proper reset methods
3. **Wrong pool type**: ThreadSafePool in single-threaded code adds overhead
4. **Forgetting to release**: Always use context managers or explicit release
5. **Premature optimization**: Profile first, optimize second
