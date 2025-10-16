# Benchmark Methodology

## Overview

This document describes the methodology used for benchmarking fastalloc.

## Environment

All benchmarks are run under controlled conditions:

- **CPU**: Performance measured on stable system load
- **Python**: CPython 3.11 (reference implementation)
- **OS**: Linux (primary), cross-platform validation on Windows/macOS
- **Tools**: pytest-benchmark for accurate timing

## Benchmark Categories

### 1. Allocation Speed

Measures raw allocation and release performance:

```python
def test_pool_allocation(benchmark):
    pool = FixedPool(MyObject, capacity=1000, pre_initialize=True)
    
    def allocate_release():
        obj = pool.get()
        pool.release(obj)
    
    benchmark(allocate_release)
```

**Metrics:**
- Mean time per operation (nanoseconds)
- Standard deviation
- Min/max times

### 2. Comparison with Naive Allocation

Compares pool performance against standard object creation:

```python
# Pool version
with pool.allocate() as obj:
    obj.process()

# Naive version
obj = MyObject()
obj.process()
del obj
```

**Metrics:**
- Speedup factor
- Memory allocation rate
- GC collection frequency

### 3. Multi-threaded Performance

Tests thread-safe and thread-local pools under contention:

```python
def threaded_benchmark():
    pool = ThreadSafePool(MyObject, capacity=100)
    
    def worker():
        for _ in range(1000):
            obj = pool.get()
            pool.release(obj)
    
    threads = [Thread(target=worker) for _ in range(10)]
    # ...
```

**Metrics:**
- Operations per second
- Lock contention overhead
- Scalability with thread count

### 4. GC Pressure

Measures impact on garbage collection:

```python
gc_count_before = gc.get_count()
# ... perform operations ...
gc_count_after = gc.get_count()
```

**Metrics:**
- GC generation 0 collections
- GC pause time
- Memory churn rate

## Acceptance Criteria

### Performance Targets

- **Object Acquisition**: < 50ns (fixed pool, pre-initialized)
- **Object Release**: < 30ns
- **GC Reduction**: >= 80% fewer collections
- **Memory Overhead**: < 10% for pools over 1000 objects
- **Thread-Safe Overhead**: < 200ns with moderate contention

### Comparison Baselines

Pools should outperform naive allocation for:

- Frequent allocate/release cycles (>100/sec)
- Objects with non-trivial construction
- Workloads with predictable capacity needs

## Running Benchmarks

### Basic Run

```bash
pytest benchmarks/ --benchmark-only
```

### Detailed Results

```bash
pytest benchmarks/ --benchmark-only --benchmark-verbose
```

### Save Results

```bash
pytest benchmarks/ --benchmark-only --benchmark-json=results.json
```

### Compare Runs

```bash
pytest benchmarks/ --benchmark-only --benchmark-compare
```

## Interpretation

### Good Results

- Mean < 50ns for allocation
- Low standard deviation (< 10% of mean)
- Linear scaling with pool capacity
- Sub-linear scaling with thread count

### Warning Signs

- High standard deviation indicates unstable performance
- Increasing mean with pool size suggests O(n) operations
- Lock contention visible as poor thread scaling

## Continuous Monitoring

Benchmarks run automatically in CI/CD:

- On every main branch commit
- On tagged releases
- Results archived for comparison

## Reproducibility

To reproduce results:

1. Use dedicated hardware (no background tasks)
2. Fix CPU frequency scaling
3. Run multiple iterations (benchmark does this automatically)
4. Report Python version and OS details
