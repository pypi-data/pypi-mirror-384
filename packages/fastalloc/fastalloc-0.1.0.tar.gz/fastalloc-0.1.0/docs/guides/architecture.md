# Architecture

## Overview

fastalloc provides a flexible architecture for object pooling with multiple pool types and allocation strategies.

## Pool Types

### FixedPool

- Fixed capacity that never grows
- O(1) allocation and release
- Best for predictable workloads

```python
from fastalloc import FixedPool

pool = FixedPool(MyObject, capacity=1000)
```

### GrowingPool

- Starts with initial capacity
- Grows according to strategy (linear or exponential)
- Optional maximum capacity limit

```python
from fastalloc import GrowingPool
from fastalloc.config import linear_growth

pool = GrowingPool(
    MyObject,
    capacity=100,
    growth_config=linear_growth(increment=50, max_capacity=1000)
)
```

### ThreadSafePool

- Uses locks for thread safety
- Shared pool across threads
- Moderate overhead from locking

```python
from fastalloc import ThreadSafePool

pool = ThreadSafePool(MyObject, capacity=1000)
```

### ThreadLocalPool

- Per-thread pool instances
- No locking overhead
- Aggregated statistics

```python
from fastalloc import ThreadLocalPool

pool = ThreadLocalPool(MyObject, capacity=100)
```

### AsyncPool

- Async/await compatible
- Uses asyncio locks
- Works with async context managers

```python
from fastalloc import AsyncPool

pool = AsyncPool(MyObject, capacity=100)

async with pool.allocate() as obj:
    await obj.process()
```

## Components

### Allocators

Internal allocation strategies:

- **StackAllocator**: LIFO stack-based (default)
- **FreelistAllocator**: Simple freelist
- **DequeAllocator**: Deque-based for efficient operations

### Handles

Object lifetime management:

- **ContextHandle**: Auto-release with context managers
- **OwnedHandle**: Explicit ownership
- **WeakHandle**: Weak reference support

### Statistics

Performance monitoring:

- Allocation/release counts
- Peak usage tracking
- Timing information
- Growth events

## Design Patterns

### Builder Pattern

Fluent API for pool configuration:

```python
pool = (Pool.builder()
    .type(MyObject)
    .capacity(1000)
    .thread_safe(True)
    .enable_statistics(True)
    .build())
```

### Decorator Pattern

Attach pools to classes:

```python
@pooled(capacity=1000, thread_safe=True)
class Worker:
    pass

Worker.pool.get()
```

## Performance Considerations

1. **Pre-initialization**: Creates objects upfront, eliminating lazy allocation overhead
2. **Reset Methods**: Cleans object state without reallocating
3. **Thread-Local Pools**: Eliminates lock contention
4. **Growth Strategies**: Balances memory usage and allocation performance
