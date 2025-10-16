# Development Guide

This guide covers development practices, testing, and contributing to ParquetFrame.

## Development Setup

### Prerequisites
- Python 3.9+
- Git
- Optional: ollama (for AI features)

### Environment Setup

```bash
# Clone the repository
git clone https://github.com/leechristophermurray/parquetframe.git
cd parquetframe

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e ".[dev,all]"

# Install pre-commit hooks
pre-commit install
```

## Project Structure

```
parquetframe/
├── src/parquetframe/           # Source code
│   ├── __init__.py
│   ├── core.py                 # Core ParquetFrame class
│   ├── cli.py                  # Command-line interface
│   ├── interactive.py          # Interactive session
│   ├── ai/                     # AI functionality
│   │   ├── agent.py            # LLM agent
│   │   └── prompts.py          # Query prompts
│   ├── datacontext/           # Data source abstraction
│   └── exceptions.py          # Error handling
├── tests/                     # Test suite
│   ├── conftest.py           # Test fixtures
│   ├── test_ai_agent.py      # AI functionality tests
│   ├── test_interactive.py   # Interactive CLI tests
│   ├── test_cli.py           # CLI tests
│   └── test_datacontext.py   # Data context tests
├── docs/                     # Documentation
└── .github/workflows/        # CI/CD workflows
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m ai          # AI-related tests
pytest -m integration # Integration tests
pytest -m slow        # Performance tests

# Run with coverage
pytest --cov=src/parquetframe --cov-report=html

# Run tests for specific functionality
pytest tests/test_ai_agent.py -v
```

### Test Categories

Tests are organized with pytest markers:

- `@pytest.mark.ai` - AI functionality tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Performance/slow tests
- `@pytest.mark.db` - Database tests

### Writing Tests

#### Test Structure
```python
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from src.parquetframe.ai.agent import LLMAgent

class TestNewFeature:
    """Test new feature functionality."""

    def test_basic_functionality(self, temp_parquet_dir):
        """Test basic feature operation."""
        # Arrange
        # Act
        # Assert

    @pytest.mark.asyncio
    async def test_async_functionality(self, mock_ollama_module):
        """Test async feature operation."""
        # Test async code
```

#### Available Fixtures
- `temp_parquet_dir` - Temporary directory with sample parquet files
- `sample_dataframe` - Sample pandas DataFrame
- `mock_ollama_module` - Mocked ollama dependencies
- `mock_console` - Mocked rich console
- `in_memory_db_engine` - SQLite in-memory database

## AI Development

### Setting up AI Development

```bash
# Install ollama (macOS)
brew install ollama

# Start ollama service
ollama serve

# Pull a model (one-time)
ollama pull llama3.2
```

### Testing AI Features

AI tests use mocking to avoid dependencies on external services:

```python
@pytest.mark.asyncio
async def test_ai_query(mock_ollama_module, mock_ollama_client):
    with patch('src.parquetframe.ai.agent.OLLAMA_AVAILABLE', True):
        agent = LLMAgent()
        # Test AI functionality
```

## Code Quality

### Pre-commit Hooks

The project uses pre-commit hooks for code quality:

- **black** - Code formatting
- **ruff** - Fast Python linter
- **mypy** - Type checking
- **Various checks** - Trailing whitespace, file endings, etc.

```bash
# Run pre-commit manually
pre-commit run --all-files

# Update hooks
pre-commit autoupdate
```

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for public methods
- Keep functions focused and small
- Use meaningful variable names

## Git Workflow

### Branch Strategy

- `main` - Production-ready code
- `develop` - Integration branch (if needed)
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Critical fixes

### Commit Messages

Use conventional commit format:
```
type(scope): description

feat(ai): add natural language query support
fix(cli): resolve argument parsing issue
docs: update API documentation
test: add integration tests for DataContext
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `style`, `chore`

### Pull Request Process

1. Create feature branch from `main`
2. Implement changes with tests
3. Ensure all tests pass
4. Update documentation
5. Create PR with clear description
6. Address review feedback
7. Merge to `main`

## CI/CD Pipeline

### Automated Testing

The GitHub Actions workflow runs:

- Tests across Python 3.9-3.13
- Multiple operating systems (Ubuntu, macOS, Windows)
- Code quality checks
- Security scanning
- Coverage reporting

### Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release tag
4. CI automatically builds and publishes to PyPI

## Adding New Features

### 1. AI Features

For new AI functionality:

1. Add to `src/parquetframe/ai/`
2. Update prompts in `prompts.py`
3. Add comprehensive tests with mocking
4. Update CLI integration
5. Document with examples

### 2. CLI Commands

For new CLI commands:

1. Add command to `cli.py`
2. Follow Click patterns
3. Add help text and examples
4. Include in tests
5. Update documentation

### 3. Data Contexts

For new data source support:

1. Create context class in `datacontext/`
2. Implement required interface
3. Add factory methods
4. Comprehensive error handling
5. Integration tests

## Performance Considerations

- Use Dask for large datasets
- Profile memory usage
- Consider lazy evaluation
- Benchmark new features
- Monitor CI performance

## Troubleshooting

### Common Issues

**AI tests failing:**
- Check ollama mocking is correct
- Ensure `OLLAMA_AVAILABLE` patches are applied

**Import errors:**
- Check optional dependencies
- Verify package installation in dev mode

**CLI tests failing:**
- Ensure Click testing patterns are followed
- Check command group structure

### Debug Tips

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use pytest debugging
pytest --pdb tests/test_module.py::test_function

# Profile code
import cProfile
cProfile.run('your_function()')
```

## Contributing Guidelines

1. **Start with an issue** - Discuss features/bugs first
2. **Write tests** - New code requires test coverage
3. **Update docs** - Include documentation changes
4. **Follow conventions** - Code style, git commits, etc.
5. **Be responsive** - Address review feedback promptly

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Click Documentation](https://click.palletsprojects.com/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [Ollama Documentation](https://ollama.ai/docs/)
