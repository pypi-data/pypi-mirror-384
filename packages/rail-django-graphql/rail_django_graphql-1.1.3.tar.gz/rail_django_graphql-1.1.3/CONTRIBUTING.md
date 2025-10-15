# Contributing to Rail Django GraphQL

Thank you for your interest in contributing to Rail Django GraphQL! This document provides guidelines and information for contributors.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please be respectful and constructive in all interactions.

## Getting Started

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/raillogistic/rail-django-graphql.git
   cd rail-django-graphql
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements-dev.txt
   pip install -e .
   ```

4. **Run Tests**
   ```bash
   python -m pytest
   ```

## 🔧 Development Workflow

### Code Style

We use several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking

Run all checks:
```bash
# Format code
black rail_django_graphql tests
isort rail_django_graphql tests

# Check linting
flake8 rail_django_graphql tests

# Type checking
mypy rail_django_graphql
```

### Testing

We use pytest for testing. Please ensure all tests pass before submitting a PR.

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=rail_django_graphql --cov-report=html

# Run specific test file
pytest tests/test_generators.py

# Run specific test
pytest tests/test_generators.py::test_type_generation
```

### Writing Tests

- Write tests for all new functionality
- Maintain test coverage above 90%
- Use descriptive test names
- Follow the Arrange-Act-Assert pattern

Example test structure:
```python
def test_schema_generation_with_custom_settings():
    """Test that schema generation respects custom settings."""
    # Arrange
    settings = TypeGeneratorSettings(enable_camel_case=True)
    
    # Act
    schema = generate_schema(settings)
    
    # Assert
    assert schema.get_type('UserType') is not None
    assert 'firstName' in str(schema)
```

## 📝 Submitting Changes

### Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code following our style guidelines
   - Add tests for new functionality
   - Update documentation if needed

3. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

4. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request**
   - Use a descriptive title
   - Explain what changes you made and why
   - Reference any related issues

### Commit Message Format

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(generators): add support for custom scalar types
fix(auth): resolve JWT token validation issue
docs(readme): update installation instructions
```

## 🐛 Reporting Issues

### Bug Reports

When reporting bugs, please include:

1. **Description**: Clear description of the issue
2. **Steps to reproduce**: Minimal steps to reproduce the bug
3. **Expected behavior**: What you expected to happen
4. **Actual behavior**: What actually happened
5. **Environment**: Python version, Django version, library version
6. **Code samples**: Minimal code that reproduces the issue

### Feature Requests

For feature requests, please include:

1. **Use case**: Why is this feature needed?
2. **Proposed solution**: How should it work?
3. **Alternatives**: Any alternative solutions considered?
4. **Additional context**: Any other relevant information

## 📚 Documentation

### Writing Documentation

- Use clear, concise language
- Include code examples
- Update relevant documentation when making changes
- Follow the existing documentation structure

### Documentation Structure

```
docs/
├── index.md              # Main documentation
├── installation.md       # Installation guide
├── configuration.md      # Configuration reference
├── api-reference.md      # API documentation
├── examples/            # Usage examples
└── advanced/            # Advanced topics
```

## 🏗️ Architecture Guidelines

### Code Organization

- Keep modules focused and cohesive
- Use clear, descriptive names
- Follow Django conventions
- Separate concerns appropriately

### Design Principles

1. **Backward Compatibility**: Maintain API compatibility when possible
2. **Performance**: Consider performance implications of changes
3. **Security**: Follow security best practices
4. **Testability**: Write testable code
5. **Documentation**: Document public APIs

### Adding New Features

1. **Design**: Consider the API design carefully
2. **Implementation**: Implement with tests
3. **Documentation**: Document the feature
4. **Examples**: Provide usage examples
5. **Migration**: Consider migration path for existing users

## 🤝 Community Guidelines

### Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

### Communication

- Be respectful and constructive
- Ask questions if you're unsure
- Help others when you can
- Use GitHub issues for bug reports and feature requests
- Use GitHub discussions for general questions

## 📋 Checklist for Contributors

Before submitting a PR, ensure:

- [ ] Code follows style guidelines (black, isort, flake8)
- [ ] All tests pass
- [ ] New functionality has tests
- [ ] Documentation is updated
- [ ] Commit messages follow conventional format
- [ ] PR description explains the changes
- [ ] No breaking changes (or clearly documented)

## 🎯 Areas for Contribution

We welcome contributions in these areas:

### High Priority
- Bug fixes
- Performance improvements
- Documentation improvements
- Test coverage improvements

### Medium Priority
- New GraphQL features
- Django compatibility updates
- Developer experience improvements
- Example applications

### Low Priority
- Code refactoring
- Additional integrations
- Advanced features

## 🔄 Release Process

Releases are handled by maintainers:

1. Version bump in `__init__.py`
2. Update `CHANGELOG.md`
3. Create GitHub release
4. Publish to PyPI (future)

## 📞 Getting Help

If you need help:

1. Check existing documentation
2. Search existing issues
3. Create a new issue with your question
4. Join our community discussions

Thank you for contributing to rail-django-graphql! 🚀