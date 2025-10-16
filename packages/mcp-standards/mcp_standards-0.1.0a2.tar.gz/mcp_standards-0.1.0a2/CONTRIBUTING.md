# Contributing to MCP Standards

Thank you for considering contributing to MCP Standards! We welcome contributions from the community.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, MCP version)

### Requesting Features

Have an idea for a new feature? Open an issue with:
- Clear description of the feature
- Use case and why it matters
- Potential implementation approach (optional)

### Contributing Code

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes**
4. **Test your changes**: Run tests and ensure they pass
5. **Commit with clear message**: Follow conventional commits
6. **Push to your fork**: `git push origin feature/your-feature-name`
7. **Open a Pull Request**

## Development Setup

### Prerequisites
- Python 3.10 or higher
- uv package manager

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/mcp-standards.git
cd mcp-standards

# Install dependencies
uv sync

# Run tests
uv run pytest
```

### Running Tests

```bash
# All tests
uv run pytest

# Specific test file
uv run pytest tests/integration/test_pattern_learning.py -v

# With coverage
uv run pytest --cov=mcp_standards
```

### Code Style

- Follow PEP 8
- Use type hints on all public functions
- Add docstrings to classes and public methods
- Keep functions focused and small
- Write tests for new features

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: Add implicit rejection detection
fix: Resolve pattern promotion bug
docs: Update README with new features
test: Add tests for rate limiting
refactor: Simplify pattern extraction logic
```

## Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Add tests for new features
4. Update CHANGELOG.md (if significant)
5. Request review from maintainers
6. Address review feedback
7. Merge once approved

## Code Review Guidelines

### For Contributors
- Be open to feedback
- Respond to comments promptly
- Keep PRs focused and small
- Explain your reasoning

### For Reviewers
- Be respectful and constructive
- Focus on code, not the person
- Suggest improvements, don't demand
- Approve when ready

## Testing Guidelines

### Test Requirements
- All new features must have tests
- Bug fixes must have regression tests
- Aim for >80% code coverage
- Test both success and failure cases

### Test Structure
```python
def test_feature_name():
    """Test description of what's being tested"""
    # Arrange
    setup_test_data()

    # Act
    result = function_under_test()

    # Assert
    assert result == expected_value
```

## Documentation

### When to Update Docs
- New features → Add to README and guides
- Breaking changes → Update migration guide
- Bug fixes → Update if behavior changed
- New MCP tools → Update API reference

### Documentation Style
- Clear and concise
- Include code examples
- Use proper markdown formatting
- Add screenshots/GIFs for UI features

## Release Process

(For maintainers)

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create git tag: `git tag -a v0.x.0 -m "Release v0.x.0"`
4. Push tag: `git push origin v0.x.0`
5. GitHub Actions will handle the release

## Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on what's best for the project
- Show empathy towards others
- Accept constructive criticism gracefully

### Communication

- GitHub Issues: Bug reports and feature requests
- GitHub Discussions: Questions and ideas
- Pull Requests: Code contributions
- Email: For private/security issues

## Security

If you discover a security vulnerability:
1. **DO NOT** open a public issue
2. Email: matt.strautmann@gmail.com
3. Include detailed description
4. We'll respond within 48 hours

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

- Check existing issues and discussions
- Ask in GitHub Discussions
- Email: matt.strautmann@gmail.com

---

**Thank you for contributing to MCP Standards! 🎉**
