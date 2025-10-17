# Contributing Guidelines

Thank you for your interest in contributing to the Quran Ayah Lookup package! We welcome contributions from the community.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/quran-ayah-lookup.git
   cd quran-ayah-lookup
   ```

3. Create a virtual environment and install development dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Write clean, readable code
- Follow PEP 8 style guidelines
- Add type hints where appropriate
- Write docstrings for functions and classes

### 3. Add Tests

- Write tests for new functionality
- Ensure existing tests still pass
- Aim for good test coverage

```bash
pytest tests/
```

### 4. Format Your Code

```bash
black src/ tests/
flake8 src/ tests/
mypy src/
```

### 5. Commit Your Changes

```bash
git add .
git commit -m "Add: Brief description of your changes"
```

Use conventional commit messages:
- `Add:` for new features
- `Fix:` for bug fixes
- `Update:` for changes to existing functionality
- `Remove:` for deleted functionality
- `Docs:` for documentation changes

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Code Style

### Python Style Guide

- Follow PEP 8
- Use Black for code formatting
- Maximum line length: 88 characters
- Use type hints for function parameters and return values

### Example:

```python
from typing import List, Optional

def search_ayah(query: str, max_results: int = 10) -> List[str]:
    """Search for ayahs matching the query.
    
    Args:
        query: The search term
        max_results: Maximum number of results to return
        
    Returns:
        List of matching ayah texts
    """
    # Implementation here
    return []
```

### Documentation

- Write clear, concise docstrings
- Use Google-style docstrings
- Update README.md if adding new features
- Add examples for new functionality

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/quran_ayah_lookup

# Run specific test file
pytest tests/test_search.py
```

### Writing Tests

- Place tests in the `tests/` directory
- Mirror the source structure in test files
- Use descriptive test names
- Test edge cases and error conditions

Example test:
```python
import pytest
from quran_ayah_lookup import QuranLookup

def test_search_returns_results():
    """Test that search returns expected results."""
    quran = QuranLookup()
    results = quran.search_text("test")
    assert isinstance(results, list)

def test_search_invalid_input():
    """Test search with invalid input."""
    quran = QuranLookup()
    with pytest.raises(ValueError):
        quran.search_text("")
```

## Reporting Issues

### Bug Reports

Please include:
- Python version
- Package version
- Minimal code example that reproduces the issue
- Expected behavior
- Actual behavior
- Error messages (if any)

### Feature Requests

Please include:
- Clear description of the feature
- Use cases and benefits
- Proposed API (if applicable)
- Implementation ideas (if you have them)

## Development Guidelines

### Branching Strategy

- `main`: Stable release branch
- `develop`: Development branch for next release
- `feature/*`: Feature branches
- `bugfix/*`: Bug fix branches
- `hotfix/*`: Critical fixes for production

### Code Review Process

1. All changes require a pull request
2. At least one review from a maintainer
3. All tests must pass
4. Code coverage should not decrease
5. Documentation must be updated for new features

### Release Process

1. Update version in `pyproject.toml` and `__init__.py`
2. Update CHANGELOG.md
3. Create release tag
4. Build and upload to PyPI

## Getting Help

- Join discussions in GitHub Issues
- Ask questions in pull requests
- Reach out to maintainers via email

## Code of Conduct

This project follows the [Python Community Code of Conduct](https://www.python.org/psf/conduct/). Please be respectful and inclusive in all interactions.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to make this package better! 🙏