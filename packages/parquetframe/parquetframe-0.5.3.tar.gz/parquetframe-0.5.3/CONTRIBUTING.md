# Contributing to ParquetFrame

Thank you for your interest in contributing to ParquetFrame! This document provides guidelines for contributing to the project.

## Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/parquetframe.git
   cd parquetframe
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Install development dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

## Development Workflow

### Code Style

We use several tools to maintain code quality:

- **Black**: Code formatting
- **Ruff**: Linting and import sorting
- **MyPy**: Type checking
- **pytest**: Testing

Run all checks locally:
```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type check
mypy src/

# Run tests
pytest
```

### Testing

- Maintain 95%+ test coverage
- Write tests for all new features
- Test both pandas and Dask code paths
- Use descriptive test names

```bash
# Run tests with coverage
pytest --cov=parquetframe --cov-report=html

# Run specific test file
pytest tests/test_core.py

# Run tests with specific markers
pytest -m "not slow"
```

### Documentation

- Update docstrings for any new or modified functions
- Add examples to docstrings where helpful
- Update README.md if adding major features
- Update CHANGELOG.md following [Keep a Changelog](https://keepachangelog.com/)

## Git Workflow

We follow conventional commits and use feature branches:

### Commit Messages

Use conventional commit format:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test changes
- `chore:` Maintenance tasks
- `refactor:` Code refactoring

Examples:
```
feat: add support for custom file extensions
fix: handle empty dataframes in to_dask conversion
docs: update API documentation for read method
test: add integration tests for file size detection
```

### Branch Naming

Use descriptive branch names:
- `feature/add-custom-extensions`
- `fix/empty-dataframe-handling`
- `docs/api-improvements`

### Pull Request Process

1. **Create a descriptive PR title** following conventional commit format
2. **Fill out the PR template** with details about your changes
3. **Ensure all CI checks pass**
4. **Request review** from maintainers
5. **Address any feedback** and update your branch as needed

## Issue Guidelines

### Bug Reports

Include:
- Python version
- ParquetFrame version
- Minimal code example to reproduce
- Expected vs actual behavior
- Error messages (if any)

### Feature Requests

Include:
- Clear description of the desired feature
- Use case and motivation
- Example of how the feature would be used
- Any alternative solutions considered

## Code Architecture

### Core Concepts

- **ParquetFrame**: Main wrapper class that delegates to pandas/Dask
- **Backend Selection**: Logic for choosing pandas vs Dask based on file size
- **File Handling**: Extension detection and path resolution
- **API Delegation**: Transparent forwarding of method calls

### Adding New Features

1. **Consider the API**: Keep it simple and consistent
2. **Support both backends**: Ensure features work with pandas and Dask
3. **Add comprehensive tests**: Cover edge cases and both backends
4. **Document thoroughly**: Include docstrings and examples
5. **Update the changelog**: Follow the established format

## Questions?

- Open an issue for general questions
- Join our discussions for design questions
- Reach out to maintainers for sensitive issues

Thank you for contributing to ParquetFrame!
