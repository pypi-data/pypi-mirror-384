# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-10-17

### Added
- Initial release of redis-cache-toolkit
- `@cached` decorator for basic function result caching
- `@cached_model` decorator for Pydantic model validation and caching
- `@geohash_cached` decorator for location-based caching
- `GeohashCacheManager` for manual geohash-based cache management
- Support for multiple Redis configurations (standalone, sentinel, cluster)
- `RedisConfig` class for flexible Redis connection management
- Utility decorators:
  - `@capture_exception_decorator` for graceful error handling
  - `@dont_unpack_list` for automatic list unpacking
  - `@default_positive_int` for default integer values
- Comprehensive test suite with pytest
- Full documentation with examples
- Type hints throughout the codebase
- CI/CD pipeline with GitHub Actions

### Features
- Automatic serialization/deserialization with pickle
- Type-safe cache keys with typed argument support
- Geohash encoding for efficient geographic data caching
- Connection pooling and singleton patterns for performance
- Configurable cache timeouts
- Custom cache key prefixes
- Support for both positional and keyword arguments

### Documentation
- Comprehensive README with usage examples
- API reference documentation
- Contributing guidelines
- Multiple example files demonstrating features
- Installation instructions for various configurations

### Testing
- Unit tests for all decorators
- Integration tests with Redis
- Tests for geohash functionality
- Connection management tests
- Helper function tests
- Test coverage > 80%

[Unreleased]: https://github.com/yourusername/redis-cache-toolkit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/redis-cache-toolkit/releases/tag/v0.1.0

