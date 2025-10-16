# Migration Guide

## Migrating from Object Pools

If you're currently using naive object creation or other pool libraries, this guide will help you migrate to fastalloc.

## From Naive Allocation

### Before

```python
def process_data(items):
    for item in items:
        processor = DataProcessor()
        result = processor.process(item)
        results.append(result)
        del processor  # May not help GC immediately
```

### After

```python
from fastalloc import Pool

processor_pool = Pool(DataProcessor, capacity=100)

def process_data(items):
    for item in items:
        with processor_pool.allocate() as processor:
            result = processor.process(item)
            results.append(result)
```

## From Other Pool Libraries

### From `reusable`

**Before:**
```python
from reusable import ReusablePool

pool = ReusablePool(MyClass, size=100)
obj = pool.get()
# use obj
pool.release(obj)
```

**After:**
```python
from fastalloc import Pool

pool = Pool(MyClass, capacity=100)
obj = pool.get()
# use obj
pool.release(obj)
```

### From `object_pool`

**Before:**
```python
from object_pool import Pool

pool = Pool(MyClass, size=100)
with pool() as obj:
    obj.use()
```

**After:**
```python
from fastalloc import Pool

pool = Pool(MyClass, capacity=100)
with pool.allocate() as obj:
    obj.use()
```

## Adding Reset Methods

For optimal performance, add reset methods to your classes:

```python
class MyClass:
    def __init__(self):
        self.data = []
        self.state = None
    
    def reset(self):
        """Called by pool when object is released."""
        self.data.clear()
        self.state = None
```

Then configure the pool:

```python
pool = Pool(MyClass, capacity=100, reset_method='reset')
```

## Thread Safety Migration

### Before (locks around object creation)

```python
lock = threading.Lock()

def get_processor():
    with lock:
        return DataProcessor()
```

### After (thread-safe pool)

```python
from fastalloc import ThreadSafePool

pool = ThreadSafePool(DataProcessor, capacity=100)

def get_processor():
    return pool.get()  # Thread-safe automatically
```

## Async Migration

### Before

```python
async def process():
    obj = MyClass()
    await obj.async_operation()
    del obj
```

### After

```python
from fastalloc import AsyncPool

pool = AsyncPool(MyClass, capacity=100)

async def process():
    async with pool.allocate() as obj:
        await obj.async_operation()
```

## Performance Tuning

### 1. Start with Fixed Pool

```python
pool = Pool(MyClass, capacity=estimated_max)
```

### 2. Add Statistics

```python
pool = Pool(MyClass, capacity=100, enable_statistics=True)

# Later, check actual usage
stats = pool.stats().snapshot()
print(f"Peak usage: {stats['peak_in_use']}")
```

### 3. Adjust Configuration

Based on statistics, choose the right pool type:

```python
# If peak < capacity: Fixed is good
pool = FixedPool(MyClass, capacity=peak_in_use)

# If peak varies: Use growing
pool = GrowingPool(
    MyClass,
    capacity=typical_usage,
    max_capacity=peak_usage * 1.2
)
```

## Common Pitfalls

### 1. Forgetting to Release

**Bad:**
```python
obj = pool.get()
obj.use()
# Forgot to release!
```

**Good:**
```python
with pool.allocate() as obj:
    obj.use()
# Auto-released
```

### 2. Holding References

**Bad:**
```python
self.cached_obj = pool.get()  # Holding reference
pool.release(self.cached_obj)  # But still holding it!
```

**Good:**
```python
with pool.allocate() as obj:
    result = obj.compute()
# Don't hold references after release
```

### 3. Wrong Pool Type

**Bad:**
```python
# Single-threaded code
pool = ThreadSafePool(MyClass, capacity=100)  # Unnecessary overhead
```

**Good:**
```python
# Single-threaded code
pool = FixedPool(MyClass, capacity=100)
```

## Gradual Migration

You can migrate gradually:

1. **Start with hot paths**: Identify frequently-created objects
2. **Add pools incrementally**: One class at a time
3. **Measure impact**: Use statistics to verify improvement
4. **Expand usage**: Apply to more classes as needed

## Validation

After migration, verify:

1. **Functionality**: All tests still pass
2. **Performance**: Benchmarks show improvement
3. **Memory**: Peak usage is acceptable
4. **GC pressure**: Fewer collection cycles
