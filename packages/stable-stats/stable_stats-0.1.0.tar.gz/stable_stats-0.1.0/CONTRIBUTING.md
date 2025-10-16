# Contributing to Stable

Thank you for your interest in contributing to Stable! This document provides guidelines and information for contributors.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

- Use a clear and descriptive title
- Describe the exact steps to reproduce the problem
- Provide specific examples to demonstrate the steps
- Describe the behavior you observed after following the steps
- Explain which behavior you expected to see instead and why
- Include screenshots and animated GIFs if possible

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- Use a clear and descriptive title
- Provide a step-by-step description of the suggested enhancement
- Provide specific examples to demonstrate the steps
- Describe the current behavior and explain which behavior you expected to see instead
- Explain why this enhancement would be useful

### Pull Requests

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Development Setup

### Prerequisites

- Python 3.7 or higher
- Git

### Setup

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/Chris-R030307/StaTable.git
   cd StaTable
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the package in development mode:
   ```bash
   pip install -e ".[dev,test]"
   ```

4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=stable --cov-report=html

# Run specific test file
pytest tests/test_core.py
```

### Code Style

We use several tools to maintain code quality:

- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

Run these tools before committing:

```bash
# Format code
black stable tests

# Sort imports
isort stable tests

# Lint code
flake8 stable tests

# Type check
mypy stable
```

### Documentation

- Update docstrings for any new functions or classes
- Update the README.md if you add new features
- Update the CHANGELOG.md for any user-facing changes

## Project Structure

```
stable/
├── stable/                 # Main package
│   ├── __init__.py
│   ├── core.py            # Core Stable class
│   ├── utils.py           # Utility functions
│   ├── adapters/          # Input adapters
│   └── exporters/         # Output exporters
├── tests/                 # Test files
├── docs/                  # Documentation
├── examples/              # Example scripts
├── .github/               # GitHub workflows
├── README.md
├── LICENSE
├── setup.py
├── pyproject.toml
└── requirements.txt
```

## Adding New Features

### New Statistical Test Support

To add support for a new statistical test:

1. Create a new adapter in `stable/adapters/`
2. Update the `detect_test_type` function in `stable/utils.py`
3. Add tests for the new adapter
4. Update documentation

### New Export Format

To add a new export format:

1. Create a new exporter in `stable/exporters/`
2. Add a method to the `Stable` class in `stable/core.py`
3. Add tests for the new exporter
4. Update documentation

## Testing Guidelines

- Write tests for all new functionality
- Aim for high test coverage
- Use descriptive test names
- Test both success and failure cases
- Use fixtures for common test data

## Release Process

1. Update version numbers in:
   - `stable/__init__.py`
   - `setup.py`
   - `pyproject.toml`

2. Update `CHANGELOG.md` with new features and bug fixes

3. Create a release tag:
   ```bash
   git tag -a v0.1.0 -m "Release version 0.1.0"
   git push origin v0.1.0
   ```

4. The GitHub Actions workflow will automatically build and publish to PyPI

## Questions?

If you have any questions about contributing, please:

- Open an issue with the "question" label
- Contact the maintainer at chris.ren@emory.edu

Thank you for contributing to Stable!
