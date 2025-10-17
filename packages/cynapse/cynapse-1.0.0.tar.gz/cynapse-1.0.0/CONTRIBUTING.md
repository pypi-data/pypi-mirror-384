# Contributing to Cynapse

Thank you for your interest in contributing to cynapse! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and constructive in all interactions. We're building a welcoming community.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected behavior vs actual behavior
- Python version and OS
- Relevant code snippets or error messages

### Suggesting Features

Feature requests are welcome! Please include:
- Clear description of the feature
- Use case and motivation
- Example API or usage if applicable

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the code style (PEP 8)
   - Add type hints
   - Write docstrings for public APIs
   - Add tests for new functionality
   - Update documentation if needed

4. **Run tests**
   ```bash
   pytest
   pytest --cov=cynapse --cov-report=html
   ```

5. **Run code quality checks**
   ```bash
   black cynapse tests examples
   isort cynapse tests examples
   mypy cynapse
   ruff check cynapse
   ```

6. **Commit your changes**
   ```bash
   git commit -m "Add feature: brief description"
   ```

7. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## Development Setup

```bash
# Clone the repository
git clone https://gitlab.com/TIVisionOSS/python/cynapse.git
cd cynapse

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev,all]"

# Run tests
pytest
```

## Code Style

- Follow PEP 8
- Use type hints (PEP 484)
- Write docstrings for all public APIs
- Use lowercase, friendly tone in comments
- Keep line length to 100 characters
- Format with `black`
- Sort imports with `isort`

### Example

```python
"""Module docstring."""

from typing import List, Optional


def my_function(param: str, count: int = 0) -> List[str]:
    """
    Brief description of what the function does.
    
    Args:
        param: Description of param
        count: Description of count (defaults to 0)
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When count is negative
    """
    # hey, this validates the input
    if count < 0:
        raise ValueError("count must be non-negative")
    
    # process and return results
    return [param] * count
```

## Testing

- Write tests for all new functionality
- Aim for 85%+ code coverage
- Test edge cases and error conditions
- Use pytest fixtures for common setup
- Mock external dependencies

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=cynapse --cov-report=term-missing

# Run specific test file
pytest tests/test_monitor.py

# Run specific test
pytest tests/test_monitor.py::test_monitor_start_stop -v
```

## Documentation

- Update README.md for user-facing changes
- Update docstrings for API changes
- Add examples for new features
- Update CHANGELOG.md

## Performance Considerations

- Monitor CPU and memory overhead
- Use profiling tools for hot paths
- Consider adaptive sampling strategies
- Cache expensive computations
- Minimize lock contention

## Security Considerations

- Never store sensitive data in logs
- Validate all external input
- Follow principle of least privilege
- Document security implications
- Test with malicious inputs

## Questions?

- Open an issue on GitLab
- Check existing issues and merge requests
- Email: oss@tivision.dev

Thank you for contributing to cynapse! 🛡️
