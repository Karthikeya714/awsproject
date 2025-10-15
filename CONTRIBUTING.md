# Contributing to Image Caption Generator

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)

## 📜 Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Respect differing viewpoints and experiences

## 🚀 Getting Started

1. **Fork the repository**
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/image-caption-gen.git
   cd image-caption-gen
   ```

3. **Set up development environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 🔄 Development Workflow

### Local Development

```bash
# Run tests
pytest tests/ -v

# Run linters
flake8 backend/ app/
black backend/ app/ --check
mypy backend/

# Format code
black backend/ app/

# Run locally
streamlit run app/streamlit_app.py
```

### With Docker

```bash
docker-compose up --build
```

## 📏 Coding Standards

### Python Style Guide

- Follow **PEP 8** style guide
- Use **type hints** for function parameters and returns
- Maximum line length: **127 characters**
- Use **docstrings** for all functions and classes

### Example:

```python
def upload_image(
    user_id: str,
    file_data: bytes,
    filename: str,
    content_type: str
) -> ImageMetadata:
    """
    Upload image to S3 and create thumbnail.
    
    Args:
        user_id: User ID
        file_data: Image file bytes
        filename: Original filename
        content_type: MIME type
        
    Returns:
        ImageMetadata with S3 URLs
    """
    # Implementation
    pass
```

### Commit Messages

Use conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Example**:
```
feat(backend): add support for GPT-4 Vision

- Implement GPT-4 Vision provider
- Add configuration options
- Update tests

Closes #123
```

## 🧪 Testing

### Unit Tests

```bash
pytest tests/test_backend.py -v --cov=backend
```

### Integration Tests

```bash
pytest tests/integration/ -v
```

### E2E Tests

```bash
export RUN_E2E_TESTS=true
export APP_URL=http://localhost:8501
pytest tests/e2e_smoke.py -v
```

### Test Coverage

- Maintain **>70% code coverage**
- Add tests for all new features
- Update tests when modifying existing code

## 🔍 Pull Request Process

### Before Submitting

1. **Update documentation**
2. **Add tests** for new functionality
3. **Run all tests** and ensure they pass
4. **Run linters** and fix all issues
5. **Update CHANGELOG.md**
6. **Rebase on main** if needed

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests pass locally
- [ ] No new warnings

## Related Issues
Closes #XXX
```

### Review Process

1. **Automated checks** must pass (CI pipeline)
2. **At least one approval** required
3. **All comments resolved**
4. **Up to date with main** branch

## 🐛 Reporting Issues

### Bug Reports

Use the bug report template:

```markdown
**Describe the bug**
Clear description of the bug

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
What you expected to happen

**Screenshots**
If applicable, add screenshots

**Environment:**
- OS: [e.g., Ubuntu 20.04]
- Python version: [e.g., 3.11]
- Browser: [e.g., Chrome 120]

**Additional context**
Any other context about the problem
```

### Feature Requests

```markdown
**Is your feature request related to a problem?**
Clear description of the problem

**Describe the solution you'd like**
Clear description of what you want to happen

**Describe alternatives you've considered**
Alternative solutions or features

**Additional context**
Any other context or screenshots
```

## 🏷️ Labels

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Documentation improvements
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention is needed
- `question`: Further information is requested

## 💬 Communication

- **GitHub Issues**: For bugs and features
- **GitHub Discussions**: For questions and ideas
- **Pull Requests**: For code contributions

## 📚 Resources

- [Python Style Guide (PEP 8)](https://pep8.org/)
- [Type Hints (PEP 484)](https://www.python.org/dev/peps/pep-0484/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)

## 🙏 Recognition

Contributors are recognized in:
- GitHub contributors page
- CHANGELOG.md
- Release notes

Thank you for contributing! 🎉
