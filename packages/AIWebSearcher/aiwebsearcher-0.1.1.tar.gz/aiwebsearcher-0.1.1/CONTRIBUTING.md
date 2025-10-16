# Contributing to Search MCP Server

Thank you for your interest in contributing to Search MCP Server! This document provides guidelines and instructions for contributing.

## 🤝 Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- A DashScope API key (for testing AI features)

### Setting Up Development Environment

1. **Fork and Clone**

```bash
git clone https://github.com/YOUR-USERNAME/Google-Search-Tool.git
cd search-mcp
```

2. **Create Virtual Environment**

```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Or using venv
python -m venv .venv
source .venv/bin/activate
```

3. **Install Dependencies**

```bash
# Install package in editable mode with dev dependencies
uv pip install -e ".[dev]"

# Or using pip
pip install -e ".[dev]"
pip install -r requirements-dev.txt
```

4. **Set Up Environment Variables**

```bash
cp .env.example .env
# Edit .env and add your API keys
```

## 🔧 Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Adding tests
- `chore/` - Maintenance tasks

### 2. Make Changes

- Write clean, readable code
- Follow Python PEP 8 style guide
- Add type hints where applicable
- Update documentation as needed
- Write or update tests for your changes

### 3. Code Quality Checks

Before committing, ensure your code passes all checks:

```bash
# Format code
black searcher/
isort searcher/

# Lint code
ruff check searcher/
pylint searcher/

# Type checking
mypy searcher/

# Run tests
pytest

# Run tests with coverage
pytest --cov=searcher --cov-report=html
```

### 4. Commit Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "feat: add Google search integration"
```

Commit message format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear title describing the change
- Detailed description of what and why
- Link to related issues (if any)
- Screenshots (if UI changes)

## 📝 Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use type hints (Python 3.10+ syntax)
- Maximum line length: 100 characters
- Use descriptive variable and function names

Example:

```python
from typing import Optional

def fetch_search_results(
    query: str,
    max_results: int = 5,
    language: str = "zh"
) -> list[dict[str, str]]:
    """
    Fetch search results from Baidu.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        language: Language code for search
        
    Returns:
        List of search result dictionaries
        
    Raises:
        ValueError: If query is empty
        RequestException: If network request fails
    """
    if not query:
        raise ValueError("Query cannot be empty")
    
    # Implementation here
    return []
```

### Documentation

- Add docstrings to all public functions and classes
- Use Google-style docstrings
- Keep README.md up to date
- Update CHANGELOG.md with your changes

### Testing

- Write tests for new features
- Maintain or improve code coverage
- Test both success and failure cases
- Use descriptive test names

Example:

```python
import pytest
from searcher.src.WebSearch.baiduSearchTool import BaiduSearchTools

def test_baidu_search_returns_valid_results():
    """Test that Baidu search returns properly formatted results."""
    tool = BaiduSearchTools()
    results = tool.baidu_search("Python programming", max_results=5)
    
    assert isinstance(results, str)
    assert "title" in results
    assert "url" in results

def test_baidu_search_handles_empty_query():
    """Test that empty query raises appropriate error."""
    tool = BaiduSearchTools()
    
    with pytest.raises(ValueError, match="Query cannot be empty"):
        tool.baidu_search("", max_results=5)
```

## 🐛 Reporting Bugs

When reporting bugs, please include:

1. **Description**: Clear description of the bug
2. **Steps to Reproduce**: Detailed steps to reproduce the issue
3. **Expected Behavior**: What you expected to happen
4. **Actual Behavior**: What actually happened
5. **Environment**: 
   - OS and version
   - Python version
   - Package version
   - Relevant dependency versions
6. **Logs/Screenshots**: Any error messages or screenshots

## 💡 Suggesting Features

We welcome feature suggestions! Please:

1. Check existing issues to avoid duplicates
2. Describe the feature clearly
3. Explain the use case and benefits
4. Provide examples if possible

## 📋 Pull Request Checklist

Before submitting a PR, ensure:

- [ ] Code follows project style guidelines
- [ ] All tests pass (`pytest`)
- [ ] Code is formatted (`black`, `isort`)
- [ ] Linting passes (`ruff`, `pylint`)
- [ ] Type checking passes (`mypy`)
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated
- [ ] Commit messages are clear
- [ ] PR description is comprehensive

## 🔍 Code Review Process

1. Maintainers will review your PR
2. Address any feedback or requested changes
3. Once approved, your PR will be merged
4. Your contribution will be included in the next release

## 📚 Additional Resources

- [Python Style Guide (PEP 8)](https://pep8.org/)
- [Type Hints (PEP 484)](https://peps.python.org/pep-0484/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)

## 🙏 Recognition

Contributors will be:
- Listed in the project README
- Credited in release notes
- Mentioned in the CONTRIBUTORS.md file

## ❓ Questions?

If you have questions:
- Open an issue with the "question" label
- Join our community discussions
- Contact the maintainers

Thank you for contributing! 🎉
