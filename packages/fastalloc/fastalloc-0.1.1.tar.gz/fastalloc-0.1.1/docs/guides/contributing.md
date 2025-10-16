# Contributing to fastalloc

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

1. **Fork and clone:**
   ```bash
   git clone https://gitlab.com/TIVisionOSS/python/fastalloc.git
   cd fastalloc
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   pip install -e .
   ```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/my-feature
# or
git checkout -b fix/my-bugfix
```

### 2. Make Changes

Follow the coding standards:

- **All comments must be lowercase**
- **Use # comment blocks above functions** with these exact headings:
  - `purpose:`
  - `params:`
  - `args:`
  - `returns:`
  - `raises:`
- Explain in simple, friendly language
- Type hints required for all functions
- Black formatting (line length 100)

Example:
```python
# purpose: gets an object from the pool for you to use.
# params: self - the pool instance.
# args: no arguments needed.
# returns: an object from the pool.
# raises: PoolEmptyError if no objects available.
def get(self) -> T:
    ...
```

### 3. Add Tests

Every new feature or bug fix needs tests:

```bash
# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=fastalloc --cov-report=html
```

Aim for 95%+ coverage.

### 4. Add Benchmarks

If performance-related, add benchmarks:

```bash
pytest benchmarks/ --benchmark-only
```

### 5. Format and Lint

```bash
# Format code
./scripts/format.sh

# Run linters
./scripts/lint.sh

# Type check
./scripts/type_check.sh
```

### 6. Update Documentation

- Add docstrings (RST format for Sphinx)
- Update relevant .rst/.md files in `docs/`
- Add examples if appropriate

### 7. Commit

Use conventional commit messages:

```
feat(pool): add exponential growth strategy
fix(stats): correct avg time calculation
docs(guide): update migration examples
test(async): add AsyncPool edge cases
```

### 8. Push and Create MR

```bash
git push origin feature/my-feature
```

Create a merge request on GitLab.

## Code Review Process

1. **Automated checks** run on CI
2. **Maintainer review** for code quality
3. **Discussion and iteration** if needed
4. **Merge** when approved

## Testing Guidelines

### Unit Tests

Test individual components:

```python
def test_fixed_pool_capacity():
    pool = FixedPool(SimpleObject, capacity=10)
    assert pool.capacity() == 10
```

### Integration Tests

Test interactions:

```python
def test_pool_lifecycle():
    pool = FixedPool(SimpleObject, capacity=10)
    objs = [pool.get() for _ in range(5)]
    for obj in objs:
        pool.release(obj)
    assert pool.available() == 5
```

### Stress Tests

Test under load:

```python
@pytest.mark.slow
def test_high_allocation_rate():
    pool = FixedPool(SimpleObject, capacity=1000, pre_initialize=True)
    for _ in range(100000):
        obj = pool.get()
        pool.release(obj)
```

### Property Tests

Use hypothesis for property-based testing:

```python
@given(st.integers(min_value=1, max_value=100))
def test_pool_capacity_property(capacity):
    pool = FixedPool(SimpleObject, capacity=capacity)
    assert pool.capacity() == capacity
```

## Documentation Guidelines

### API Documentation

Use Sphinx-compatible docstrings:

```python
def get(self) -> T:
    """Acquire an object from the pool.
    
    Returns:
        T: An object from the pool.
        
    Raises:
        PoolEmptyError: If no objects are available.
        PoolClosedError: If the pool is closed.
    """
```

### Guides and Tutorials

- Write clearly and concisely
- Include code examples
- Test all examples
- Use Markdown or RST

## Performance Considerations

When optimizing:

1. **Benchmark first** - prove there's a problem
2. **Profile** - find the actual bottleneck
3. **Optimize** - make targeted changes
4. **Verify** - benchmarks show improvement

## Release Process

Maintainers handle releases:

1. Update version in `__version__.py`
2. Update CHANGELOG.md
3. Create git tag
4. CI builds and deploys to PyPI

## Getting Help

- Open an issue for bugs or feature requests
- Discuss in merge requests
- Email: eshanized@proton.me

## Code of Conduct

Be respectful and professional. See [CODE_OF_CONDUCT.md](../../CODE_OF_CONDUCT.md).

## License

By contributing, you agree your contributions will be dual-licensed under MIT OR Apache-2.0.
