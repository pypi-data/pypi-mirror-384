# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2025-10-15

### Fixed
- Fixed `size()` method to correctly track in-use objects by always recording stats
- Fixed PyPI classifier - replaced invalid 'Topic :: System :: Memory Management'
- Exported `linear_growth` and `exponential_growth` from config module
- Applied code formatting with black and isort

### Changed
- All pool implementations now always track current_in_use for accurate size reporting
- Adjusted async concurrent test capacity to match pool size

## [0.1.0] - 2025-10-15

### Added
- Initial implementation of fastalloc memory pool library
- Fixed-size pool implementation
- Growing pool with linear and exponential strategies
- Thread-safe pool with locking
- Thread-local pool for per-thread allocation
- Async pool with async/await support
- Context manager handles for safe resource management
- Builder pattern for pool configuration
- `@pooled` decorator for class-level pool attachment
- Statistics collection and reporting
- Comprehensive test suite (80% coverage, 57 tests)
- Performance benchmarks
- Complete documentation with Sphinx
- CI/CD pipeline for GitLab
- Examples for common use cases
- Full type hint support
- Production-ready packaging

[Unreleased]: https://gitlab.com/TIVisionOSS/python/fastalloc/-/compare/v0.1.1...HEAD
[0.1.1]: https://gitlab.com/TIVisionOSS/python/fastalloc/-/compare/v0.1.0...v0.1.1
[0.1.0]: https://gitlab.com/TIVisionOSS/python/fastalloc/-/tags/v0.1.0
