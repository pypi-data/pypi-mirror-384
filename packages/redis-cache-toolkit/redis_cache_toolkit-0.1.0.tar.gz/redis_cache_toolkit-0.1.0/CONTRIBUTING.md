# Contributing to Redis Cache Toolkit

First off, thank you for considering contributing to Redis Cache Toolkit! It's people like you that make this tool better for everyone.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)

## Code of Conduct

This project and everyone participating in it is governed by our commitment to providing a welcoming and inspiring community for all. Please be respectful and constructive in your interactions.

### Our Standards

- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples** (code snippets, config files, etc.)
- **Describe the behavior you observed** and what you expected
- **Include error messages and stack traces**
- **Specify your environment**:
  - OS and version
  - Python version
  - Redis version
  - redis-cache-toolkit version

**Bug Report Template:**

```markdown
## Description
[Clear description of the bug]

## Steps to Reproduce
1. ...
2. ...
3. ...

## Expected Behavior
[What you expected to happen]

## Actual Behavior
[What actually happened]

## Environment
- OS: [e.g., Ubuntu 20.04]
- Python: [e.g., 3.10.5]
- Redis: [e.g., 7.0.5]
- redis-cache-toolkit: [e.g., 0.1.0]

## Additional Context
[Any other relevant information]
```

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- **Use a clear and descriptive title**
- **Provide a detailed description** of the suggested enhancement
- **Explain why this enhancement would be useful**
- **Include code examples** if applicable
- **List any alternatives** you've considered

### Your First Code Contribution

Unsure where to begin? Look for issues tagged with:

- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `documentation` - Documentation improvements

### Pull Requests

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Development Setup

### Prerequisites

- Python 3.8+
- Redis server (for running tests)
- Git

### Setup Instructions

1. **Clone your fork:**
   ```bash
   git clone https://github.com/yourusername/redis-cache-toolkit.git
   cd redis-cache-toolkit
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install pre-commit hooks (optional but recommended):**
   ```bash
   pre-commit install
   ```

5. **Start Redis server:**
   ```bash
   # macOS with Homebrew
   brew services start redis
   
   # Ubuntu/Debian
   sudo systemctl start redis
   
   # Docker
   docker run -d -p 6379:6379 redis:latest
   ```

6. **Verify setup:**
   ```bash
   pytest
   ```

## Pull Request Process

### Before Submitting

1. **Update tests**: Add or update tests for your changes
2. **Run the test suite**: `pytest`
3. **Run linters**: `black .` and `ruff .`
4. **Update documentation**: If you changed APIs or added features
5. **Update CHANGELOG**: Add an entry under "Unreleased"

### PR Guidelines

- **Keep PRs focused**: One feature or fix per PR
- **Write clear commit messages**: Follow conventional commits style
- **Update documentation**: Keep docs in sync with code
- **Add tests**: Maintain or improve test coverage
- **Pass CI checks**: All tests must pass

### Commit Message Format

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, missing semicolons, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Changes to build process or auxiliary tools

**Examples:**
```
feat(decorators): add support for async functions

Add @async_cached decorator for async function caching.
This allows users to cache async functions with the same
ease as synchronous functions.

Closes #123
```

```
fix(geohash): correct precision calculation for edge cases

Fixed an issue where geohash precision calculation was
incorrect for coordinates near the poles.

Fixes #456
```

## Coding Standards

### Style Guide

We use:
- **Black** for code formatting (line length: 100)
- **Ruff** for linting
- **mypy** for type checking

Run formatters and linters:
```bash
# Format code
black redis_cache_toolkit tests examples

# Lint code
ruff redis_cache_toolkit tests examples

# Type check
mypy redis_cache_toolkit
```

### Code Style

- Use type hints for all function signatures
- Write docstrings for all public functions and classes
- Keep functions focused and single-purpose
- Use descriptive variable names
- Add comments for complex logic

### Example Code Style

```python
def cache_function(
    timeout: int = 60,
    key_prefix: Optional[str] = None,
    redis_config: Optional[RedisConfig] = None,
) -> Callable:
    """
    Cache function results in Redis.
    
    This decorator caches the return value of a function using
    Redis as the backend storage.
    
    Args:
        timeout: Cache timeout in seconds (default: 60)
        key_prefix: Custom prefix for cache keys
        redis_config: Redis configuration instance
        
    Returns:
        Decorated function
        
    Examples:
        >>> @cache_function(timeout=300)
        ... def expensive_operation(x: int) -> int:
        ...     return x * 2
        
        >>> result = expensive_operation(5)  # Executes function
        >>> result = expensive_operation(5)  # Returns from cache
    """
    # Implementation...
```

## Testing Guidelines

### Writing Tests

- Write tests for all new features
- Test edge cases and error conditions
- Use descriptive test names
- Keep tests focused and independent
- Use fixtures for common setup

### Test Structure

```python
class TestFeatureName:
    """Tests for feature name."""
    
    def test_basic_functionality(self, redis_conn):
        """Test basic feature usage."""
        # Arrange
        expected = "value"
        
        # Act
        result = some_function()
        
        # Assert
        assert result == expected
    
    def test_edge_case(self, redis_conn):
        """Test edge case handling."""
        # ...
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=redis_cache_toolkit --cov-report=html

# Run specific test file
pytest tests/test_decorators.py

# Run specific test
pytest tests/test_decorators.py::TestCachedDecorator::test_basic_caching

# Run with verbose output
pytest -v

# Run tests matching pattern
pytest -k "geohash"
```

### Coverage Requirements

- Maintain minimum 80% test coverage
- Critical paths should have 100% coverage
- Check coverage report: `open htmlcov/index.html`

## Documentation

### Docstring Format

We use Google-style docstrings:

```python
def function_name(param1: int, param2: str) -> bool:
    """
    Short description of the function.
    
    Longer description if needed. Can span multiple
    paragraphs if necessary.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param1 is negative
        KeyError: When param2 is not found
        
    Examples:
        >>> result = function_name(42, "test")
        >>> print(result)
        True
    """
    # Implementation...
```

### Updating Documentation

When making changes:

1. **Update README.md**: For new features or API changes
2. **Update docstrings**: Keep them in sync with code
3. **Update examples**: Add examples for new features
4. **Update CHANGELOG**: Document all changes

### Building Documentation Locally

```bash
# If we add sphinx later
cd docs
make html
open _build/html/index.html
```

## Release Process

### Version Numbers

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

### Release Checklist

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Run full test suite
4. Create git tag: `git tag -a v0.1.0 -m "Release v0.1.0"`
5. Push tag: `git push origin v0.1.0`
6. GitHub Actions will automatically publish to PyPI

## Questions?

Feel free to:
- Open an issue for questions
- Start a discussion in GitHub Discussions
- Reach out to maintainers

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project README

Thank you for contributing! 🎉

