# Contributing to Media Crawler

Thank you for your interest in contributing to Media Crawler! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all. Please be respectful and constructive in your interactions.

### Our Standards

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/HasanRagab/media-crawler.git
   cd media-crawler
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/originaluser/media-crawler.git
   ```

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Chrome/Chromium browser
- ChromeDriver
- FFmpeg

### Setup Steps

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install -e ".[dev]"

# Verify installation
pytest
```

### Development Dependencies

The `[dev]` extra includes:
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `black` - Code formatter
- `flake8` - Linter
- `mypy` - Type checker

## How to Contribute

### Types of Contributions

We welcome:

1. **Bug Reports** - Report bugs via GitHub Issues
2. **Feature Requests** - Suggest new features
3. **Bug Fixes** - Submit PRs for bug fixes
4. **New Features** - Implement new functionality
5. **Documentation** - Improve or add documentation
6. **Tests** - Add or improve test coverage
7. **Code Refactoring** - Improve code quality

### Before You Start

1. **Check existing issues** to avoid duplication
2. **Discuss major changes** in an issue first
3. **Keep changes focused** - one feature/fix per PR
4. **Update documentation** for new features

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some modifications:

- **Line length**: 100 characters max
- **Quotes**: Double quotes for strings
- **Indentation**: 4 spaces (no tabs)

### Code Formatting

Use **black** for automatic formatting:

```bash
# Format all files
black .

# Format specific file
black media_crawler/crawler.py

# Check without modifying
black --check .
```

### Linting

Use **flake8** for linting:

```bash
# Lint all files
flake8 .

# Lint specific file
flake8 media_crawler/crawler.py
```

Configuration in `setup.cfg`:
```ini
[flake8]
max-line-length = 100
exclude = .git,__pycache__,.venv
ignore = E203,W503
```

### Type Hints

Use type hints for all functions and methods:

```python
from typing import List, Optional

def process_urls(urls: List[str], max_depth: int = 2) -> Optional[dict]:
    """Process URLs and return results."""
    pass
```

Run **mypy** for type checking:

```bash
mypy media_crawler/
```

### Docstrings

Use Google-style docstrings:

```python
def example_function(param1: str, param2: int) -> bool:
    """
    Brief description of function.
    
    Longer description if needed, explaining the function's behavior,
    use cases, and any important notes.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param2 is negative
        
    Example:
        >>> example_function("test", 5)
        True
    """
    pass
```

### Code Organization

#### Classes

```python
class MyClass:
    """Class docstring."""
    
    def __init__(self, param: str):
        """Initialize with parameter."""
        self.param = param
    
    def public_method(self) -> str:
        """Public method."""
        return self._private_method()
    
    def _private_method(self) -> str:
        """Private method (single underscore)."""
        return self.param
```

#### Imports

Order imports as follows:

```python
# Standard library
import os
import sys
from typing import List, Optional

# Third-party packages
import requests
from bs4 import BeautifulSoup

# Local imports
from .config import ApplicationConfig
from .exceptions import CrawlerException
```

Use **isort** to organize imports:

```bash
isort media_crawler/
```

## Testing

### Writing Tests

Create tests in the `tests/` directory:

```python
# tests/test_crawler.py
import pytest
from media_crawler import Crawler, ApplicationConfig

def test_crawler_initialization():
    """Test crawler initializes correctly."""
    config = ApplicationConfig.for_youtube()
    assert config.platform.name == "YouTube"

def test_crawler_with_invalid_depth():
    """Test crawler rejects invalid depth."""
    with pytest.raises(ValueError):
        config = CrawlerConfig(max_depth=-1)
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_crawler.py

# Run specific test
pytest tests/test_crawler.py::test_crawler_initialization

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=media_crawler --cov-report=html

# Run only failed tests
pytest --lf
```

### Test Coverage

Aim for high test coverage:

```bash
# Generate coverage report
pytest --cov=media_crawler --cov-report=term-missing

# Generate HTML report
pytest --cov=media_crawler --cov-report=html
# Open htmlcov/index.html in browser
```

### Test Best Practices

1. **Use fixtures** for common setup:
   ```python
   @pytest.fixture
   def crawler_config():
       return ApplicationConfig.for_youtube()
   ```

2. **Use parametrize** for multiple inputs:
   ```python
   @pytest.mark.parametrize("depth,expected", [
       (0, 0),
       (1, 1),
       (2, 2),
   ])
   def test_depth(depth, expected):
       assert depth == expected
   ```

3. **Mock external dependencies**:
   ```python
   from unittest.mock import Mock, patch
   
   @patch('media_crawler.webdriver.Chrome')
   def test_with_mock(mock_chrome):
       mock_chrome.return_value = Mock()
       # test code
   ```

## Documentation

### Documenting Code

1. **Module docstrings** at file top
2. **Class docstrings** after class definition
3. **Method docstrings** for all public methods
4. **Inline comments** for complex logic

### Updating Documentation

When adding features:

1. Update `README.md` with examples
2. Update `docs/API.md` with API details
3. Update `docs/ARCHITECTURE.md` if architecture changes
4. Add examples to `examples/` directory

### Documentation Format

Use Markdown for all documentation:

- Clear headings structure
- Code blocks with syntax highlighting
- Links to related sections
- Examples for complex features

## Pull Request Process

### Before Submitting

1. **Update from upstream**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all checks**:
   ```bash
   make lint
   make typecheck
   make test
   ```

3. **Update documentation**

4. **Commit with clear messages**:
   ```bash
   git commit -m "Add feature X"
   
   # Detailed commit message
   git commit -m "Add feature X
   
   - Implement functionality Y
   - Add tests for Z
   - Update documentation"
   ```

### Submitting PR

1. **Push to your fork**:
   ```bash
   git push origin feature/your-feature
   ```

2. **Create pull request** on GitHub

3. **Fill PR template**:
   - Description of changes
   - Related issues
   - Testing performed
   - Screenshots (if UI changes)

4. **Wait for review**

### PR Guidelines

- **Keep PRs focused** - one feature/fix per PR
- **Write clear descriptions**
- **Reference related issues** - "Fixes #123"
- **Respond to feedback** promptly
- **Keep commits clean** - squash if needed

### Review Process

1. Maintainers will review your PR
2. Address any requested changes
3. Once approved, PR will be merged
4. Your contribution will be credited

## Issue Guidelines

### Reporting Bugs

Use the bug report template:

```markdown
**Description**
Clear description of the bug

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
What you expected to happen

**Actual behavior**
What actually happened

**Environment**
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.10]
- Package version: [e.g., 1.0.3]

**Additional context**
Any other relevant information
```

### Feature Requests

Use the feature request template:

```markdown
**Is your feature request related to a problem?**
Clear description of the problem

**Describe the solution you'd like**
Clear description of desired behavior

**Describe alternatives you've considered**
Alternative solutions or features

**Additional context**
Any other relevant information
```

### Asking Questions

- Check documentation first
- Search existing issues
- Use clear, descriptive titles
- Provide context and examples

## Development Workflow

### Branch Naming

Use descriptive branch names:

```bash
feature/add-spotify-support
bugfix/fix-download-error
docs/update-api-documentation
refactor/improve-error-handling
```

### Commit Messages

Follow conventional commits:

```
feat: add Spotify support
fix: resolve download timeout issue
docs: update API documentation
refactor: simplify error handling
test: add tests for link extraction
chore: update dependencies
```

### Release Process

Maintainers handle releases:

1. Update version in `setup.py` and `__init__.py`
2. Update `CHANGELOG.md`
3. Create git tag: `v1.0.3`
4. Build and publish to PyPI
5. Create GitHub release

## Getting Help

If you need help:

1. **Documentation** - Check README and docs/
2. **Issues** - Search existing issues
3. **Discussions** - Use GitHub Discussions
4. **Email** - Contact maintainers

## Recognition

Contributors are recognized:

- Listed in `CONTRIBUTORS.md`
- Mentioned in release notes
- GitHub contributor badge

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Media Crawler! 🎉
