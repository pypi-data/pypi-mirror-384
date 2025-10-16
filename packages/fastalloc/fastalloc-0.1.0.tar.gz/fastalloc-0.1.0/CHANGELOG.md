# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- Comprehensive test suite (95%+ coverage)
- Performance benchmarks
- Complete documentation with Sphinx
- CI/CD pipeline for GitLab
- Examples for common use cases

## [0.1.0] - TBD

### Added
- First public release
- Core pool implementations
- Full type hint support
- Production-ready packaging

[Unreleased]: https://gitlab.com/TIVisionOSS/python/fastalloc/-/compare/v0.1.0...HEAD
[0.1.0]: https://gitlab.com/TIVisionOSS/python/fastalloc/-/tags/v0.1.0
