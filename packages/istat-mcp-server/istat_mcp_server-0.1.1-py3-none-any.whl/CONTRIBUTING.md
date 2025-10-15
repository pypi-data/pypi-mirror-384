# Contributing to ISTAT MCP Server

Thank you for your interest in contributing to the ISTAT MCP Server! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

This project follows a code of conduct to ensure a welcoming environment for all contributors. Please be respectful and constructive in all interactions.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/istat-mcp-server.git
   cd istat-mcp-server
   ```
3. **Add the upstream remote**:
   ```bash
   git remote add upstream https://github.com/Halpph/istat-mcp-server.git
   ```

## Development Setup

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Git

### Install Dependencies

```bash
# Install all dependencies including dev dependencies
uv sync

# Or with pip
pip install -e ".[dev]"
```

### Verify Installation

```bash
# Run tests to ensure everything is working
uv run pytest

# Run the server in development mode
uv run python main.py
```

## Project Structure

```
istat-mcp-server/
├── main.py                    # Main MCP server implementation
├── test_main.py              # Comprehensive test suite
├── pyproject.toml            # Project metadata and dependencies
├── uv.lock                   # Dependency lock file
├── README.md                 # User-facing documentation
├── CONTRIBUTING.md           # This file
├── LICENSE                   # MIT License
├── docs/                     # Additional documentation
│   ├── TESTING.md           # Testing guide
│   └── ISTATAPI_REFERENCE.md # Reference documentation
└── examples/                 # Example configurations
    └── gemini-extension.json # Example Gemini config
```

## Development Workflow

### 1. Create a Feature Branch

```bash
# Update your local main branch
git checkout main
git pull upstream main

# Create a new branch for your feature
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Write clean, readable code
- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed
- Keep commits atomic and well-described

### 3. Test Your Changes

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=main --cov-report=term-missing

# Ensure coverage stays above 80%
uv run pytest --cov=main --cov-report=html
```

### 4. Commit Your Changes

```bash
# Stage your changes
git add .

# Commit with a descriptive message
git commit -m "Add feature: brief description"
```

Use clear commit messages:
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **test**: Test additions or changes
- **refactor**: Code refactoring
- **chore**: Maintenance tasks

Examples:
```
feat: add support for dataset metadata filtering
fix: handle timeout errors in data retrieval
docs: update installation instructions for Windows
test: add tests for error handling in get_data
```

## Testing

### Running Tests

See [docs/TESTING.md](docs/TESTING.md) for comprehensive testing documentation.

Quick reference:
```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=main --cov-report=html

# Specific test class
uv run pytest test_main.py::TestDatasetDiscovery -v

# Specific test function
uv run pytest test_main.py::TestDatasetDiscovery::test_search_datasets -v
```

### Writing Tests

When adding new features:

1. **Add tests first** (TDD approach recommended)
2. **Test both success and error cases**
3. **Mock external API calls** to avoid network dependencies
4. **Verify return types and data structures**
5. **Maintain or improve test coverage**

Example test:
```python
from unittest.mock import patch

@patch("main.discovery.get_available_dataflows")
def test_new_feature(mock_get_dataflows):
    # Setup
    mock_get_dataflows.return_value = expected_data

    # Execute
    result = new_feature_function("param")

    # Verify
    assert result["status"] == "success"
    assert len(result["data"]) > 0
    mock_get_dataflows.assert_called_once_with("param")
```

## Code Style

### Python Style Guidelines

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guide
- Use type hints where appropriate
- Write docstrings for functions and classes
- Keep functions focused and modular
- Use meaningful variable and function names

### Function Documentation

```python
def example_function(param1: str, param2: int) -> dict:
    """
    Brief description of what the function does.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Dictionary containing the result with structure:
        {
            "status": "success" | "error",
            "data": ...
        }

    Raises:
        ValueError: When param2 is negative
    """
    pass
```

### MCP Tool Guidelines

When adding new MCP tools:

1. **Clear descriptions**: Explain what the tool does
2. **Validate inputs**: Check parameters before processing
3. **Handle errors gracefully**: Return helpful error messages
4. **Use consistent return format**: Follow existing patterns
5. **Add logging**: Include debug logging for troubleshooting

## Submitting Changes

### Pull Request Process

1. **Update your branch** with the latest upstream changes:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create a Pull Request** on GitHub with:
   - Clear title describing the change
   - Detailed description of what changed and why
   - Reference to any related issues
   - Screenshots/examples if applicable

### Pull Request Checklist

Before submitting, ensure:

- [ ] Code follows project style guidelines
- [ ] All tests pass (`uv run pytest`)
- [ ] Test coverage maintained or improved
- [ ] Documentation updated (README, docstrings, etc.)
- [ ] Commit messages are clear and descriptive
- [ ] Branch is up to date with main
- [ ] No merge conflicts

### Review Process

- Maintainers will review your PR
- Address any feedback or requested changes
- Once approved, your PR will be merged

## Reporting Issues

### Bug Reports

When reporting bugs, include:

- **Clear title** describing the issue
- **Steps to reproduce** the problem
- **Expected behavior** vs actual behavior
- **Environment details**: OS, Python version, dependencies
- **Error messages** and stack traces if applicable
- **Minimal example** that demonstrates the issue

### Feature Requests

When requesting features:

- **Describe the feature** and its use case
- **Explain why** it would be valuable
- **Provide examples** of how it would work
- **Consider alternatives** you've thought about

### Questions

For questions:

- Check existing [issues](https://github.com/Halpph/istat-mcp-server/issues) first
- Check the [README](README.md) and [docs](docs/)
- If still unclear, open a new issue with the "question" label

## Development Tips

### Testing Against a Real Claude Desktop

1. Build your changes:
   ```bash
   uv sync
   ```

2. Update your Claude Desktop config to point to your development directory:
   ```json
   {
     "mcpServers": {
       "istat-dev": {
         "command": "uv",
         "args": [
           "--directory",
           "/path/to/your/istat-mcp-server",
           "run",
           "python",
           "main.py"
         ]
       }
     }
   }
   ```

3. Restart Claude Desktop and test your changes

### Debugging

Enable debug mode for detailed error traces:

```json
{
  "mcpServers": {
    "istat": {
      "command": "uv",
      "args": ["--directory", "/path/to/istat-mcp-server", "run", "python", "main.py"],
      "env": {
        "MCP_DEBUG": "true"
      }
    }
  }
}
```

### Adding New Dependencies

When adding dependencies:

1. Add to `pyproject.toml` under `[project.dependencies]`
2. Run `uv sync` to update the lock file
3. Document any new required setup in README

## Getting Help

- **Documentation**: Check [README.md](README.md) and [docs/](docs/)
- **Issues**: Search [existing issues](https://github.com/Halpph/istat-mcp-server/issues)
- **Discussions**: Start a [discussion](https://github.com/Halpph/istat-mcp-server/discussions)
- **ISTAT API**: See [ISTAT API docs](https://www.istat.it/en/web-services)
- **istatapi**: Check [istatapi guide](https://github.com/ondata/guida-api-istat)

## Recognition

Contributors will be recognized in:
- GitHub contributors list
- Release notes for significant contributions
- README acknowledgments section (for major contributions)

Thank you for contributing to ISTAT MCP Server!
