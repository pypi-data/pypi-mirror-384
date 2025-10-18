# Contributing to Polyspark

Thank you for your interest in contributing to Polyspark! This document provides guidelines and instructions for contributing.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Basic understanding of PySpark and data factories

### Development Setup

1. Fork the repository on GitHub

2. Clone your fork:
```bash
git clone https://github.com/YOUR_USERNAME/polyspark.git
cd polyspark
```

3. Install development dependencies:
```bash
pip install -r requirements-dev.txt
pip install -e .
```

4. Create a branch for your changes:
```bash
git checkout -b feature/your-feature-name
```

## Development Workflow

### Running Tests

Run the test suite:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=polyspark --cov-report=html --cov-report=term
```

Or use the Makefile:
```bash
make test
make test-cov
```

### Code Quality

We use several tools to maintain code quality:

- **Black** for code formatting
- **Ruff** for linting
- **MyPy** for type checking

Run all checks:
```bash
make lint
```

Format code:
```bash
make format
```

### Writing Tests

- All new features should include tests
- Tests use pytest
- Place tests in the `tests/` directory
- Name test files `test_*.py`
- Use descriptive test names

Example:
```python
def test_build_dataframe_with_nested_struct(spark):
    """Test DataFrame generation with nested structs."""
    # Your test code here
    pass
```

### Documentation

- Update README.md for new features
- Add docstrings to all public functions and classes
- Include usage examples
- Update CHANGELOG.md

## Pull Request Process

1. **Update Tests**: Ensure all tests pass
2. **Update Documentation**: Add relevant documentation
3. **Update CHANGELOG**: Add entry under "Unreleased" section
4. **Code Quality**: Run linters and formatters
5. **Commit Messages**: Use clear, descriptive commit messages
6. **Push Changes**: Push to your fork
7. **Create PR**: Open a pull request against the main branch

### Commit Message Guidelines

Use clear and descriptive commit messages:

```
Add support for TypedDict schema inference

- Implement typed_dict_to_struct_type function
- Add tests for TypedDict conversion
- Update documentation with TypedDict examples
```

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How has this been tested?

## Checklist
- [ ] Tests pass locally
- [ ] Added/updated tests
- [ ] Updated documentation
- [ ] Updated CHANGELOG.md
- [ ] Code follows style guidelines
```

## Code Style

### Python Style

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use meaningful variable names

### Example:

```python
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class User:
    """Represents a user in the system.
    
    Attributes:
        id: Unique user identifier.
        username: User's username.
        email: User's email address.
    """
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
```

## Areas for Contribution

### Good First Issues

- Documentation improvements
- Example scripts
- Test coverage improvements
- Bug fixes

### Feature Ideas

- Support for more PySpark types
- Custom data generators
- Performance optimizations
- Additional schema validation
- Integration with other factory libraries

## Questions?

If you have questions:

1. Check existing issues on GitHub
2. Review documentation
3. Open a new issue with your question

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Help others learn

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be recognized in:
- CHANGELOG.md
- GitHub contributors page
- Release notes

Thank you for contributing to Polyspark! 🚀

