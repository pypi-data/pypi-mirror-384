# Contributing to fastalloc

Thank you for your interest in contributing to fastalloc! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

1. Fork the repository on GitLab
2. Clone your fork locally
3. Create a new branch for your feature or bugfix
4. Make your changes
5. Run tests and linters
6. Commit and push your changes
7. Open a merge request

## Development Setup

```bash
# Clone repository
git clone https://gitlab.com/TIVisionOSS/python/fastalloc.git
cd fastalloc

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt
pip install -e .
```

## Code Style

### Python Style
- Follow PEP 8
- Use Black for formatting
- Use isort for import sorting
- Maximum line length: 100 characters
- Full type hints required

### Comment Style (IMPORTANT)
All comments in Python files must follow these rules:

1. **All comments must be lowercase**
2. **Function/method comments must use `#` (not docstrings)**
3. **Required sections in this exact order:**
   - `purpose:` - What the function does (explain like to a 12-year-old)
   - `params:` - Parameter descriptions
   - `args:` - Positional vs keyword usage notes
   - `returns:` - Return value description
   - `raises:` - Exceptions that can be raised

Example:
```python
# purpose: grabs an object from the pool so you can use it temporarily.
# params: none.
# args: no arguments needed, just call it!
# returns: an object from the pool that you borrowed.
# raises: PoolEmptyError if no objects are available.
def get(self):
    ...
```

## Testing

### Running Tests
```bash
# All tests
./scripts/test_all.sh

# Specific test file
pytest tests/unit/test_fixed_pool.py

# With coverage
pytest --cov=fastalloc --cov-report=html
```

### Test Requirements
- Minimum 95% coverage
- Unit tests for all new functions
- Integration tests for new features
- Property tests for invariants
- Stress tests for performance-critical code

### Writing Tests
- Use descriptive test names: `test_fixed_pool_raises_empty_error_when_exhausted`
- Follow AAA pattern: Arrange, Act, Assert
- Use fixtures from `conftest.py`
- Add docstrings to test functions

## Benchmarks

```bash
# Run benchmarks
./scripts/benchmark.sh

# Compare with baseline
pytest benchmarks/ --benchmark-compare
```

New features should include benchmarks if they affect performance.

## Type Checking

```bash
./scripts/type_check.sh
```

All code must pass mypy in strict mode.

## Linting

```bash
./scripts/lint.sh
```

Code must pass all linters:
- black
- isort
- flake8
- pylint
- mypy

## Documentation

- Update docstrings for all public APIs
- Update relevant .rst files in `docs/`
- Add examples to `examples/` directory
- Update CHANGELOG.md
- Update README.md if needed

Build docs locally:
```bash
cd docs
make html
```

## Commit Messages

Follow conventional commits:

```
type(scope): short description

Longer description if needed

Fixes #123
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding tests
- `chore`: Maintenance tasks
- `ci`: CI/CD changes

## Pull Request Process

1. **Update Tests**: Add/update tests for your changes
2. **Update Docs**: Update relevant documentation
3. **Run Checks**: Ensure all tests and linters pass
4. **Update Changelog**: Add entry to CHANGELOG.md
5. **Describe Changes**: Provide clear PR description
6. **Link Issues**: Reference related issues
7. **Request Review**: Tag maintainers for review

### PR Checklist
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] Coverage >= 95%
- [ ] Type checking passes
- [ ] Linting passes
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Commit messages follow convention

## Feature Requests

Open an issue with:
- Clear description of the feature
- Use cases and benefits
- Proposed API (if applicable)
- Willingness to implement

## Bug Reports

Open an issue with:
- Description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Python version and OS
- Minimal code example
- Stack trace (if applicable)

## Performance Improvements

For performance-related PRs:
- Include benchmarks showing improvement
- Explain the optimization technique
- Document any trade-offs
- Ensure no functionality regression

## Questions?

- Open a discussion on GitLab
- Email: eshanized@proton.me

Thank you for contributing to fastalloc!
