# Contributing to rackfish

Thank you for your interest in contributing to rackfish! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and constructive in all interactions with the project community.

## How to Contribute

### Reporting Bugs

- Check if the bug has already been reported in Issues
- Include detailed steps to reproduce
- Include Python version, OS, and BMC vendor/model
- Provide relevant error messages and logs

### Suggesting Features

- Open an issue describing the feature
- Explain the use case and benefits
- Provide examples if possible

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest tests/`)
6. Update documentation as needed
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/rackfish.git
cd rackfish

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run linting
ruff check rackfish/
black --check rackfish/
mypy rackfish/
```

## Coding Standards

### Style Guide

- Follow PEP 8
- Use Black for code formatting (line length: 100)
- Use Ruff for linting
- Use type hints where appropriate
- Write docstrings for public functions and classes

### Code Organization

- Keep functions focused and small
- Use meaningful variable names
- Add comments for complex logic
- Maintain backward compatibility when possible

### Testing

- Write tests for all new functionality
- Maintain or improve test coverage
- Use descriptive test names
- Mock external dependencies (BMC connections)
- Test edge cases and error conditions

### Documentation

- Update README.md for major changes
- Add examples to `docs/EXAMPLES.md`
- Update `docs/USE_CASES.md` for new operations
- Add docstrings with examples
- Update CHANGELOG.md

## Architecture Guidelines

See `.github/copilot-instructions.md` for detailed architecture documentation:

- Lazy loading semantics
- OEM/Links surfacing mechanism
- Action binding and validation
- Collection protocols
- Recursion guard implementation

## Review Process

1. All PRs require review before merging
2. Automated tests must pass
3. Code coverage should not decrease
4. Documentation must be updated
5. CHANGELOG.md must be updated

## Release Process

1. Update version in `rackfish/__init__.py` and `pyproject.toml`
2. Update CHANGELOG.md
3. Create a git tag
4. Build and publish to PyPI

## Questions?

Feel free to open an issue for questions or discussion.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
