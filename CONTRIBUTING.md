# Contributing to CodeTruth

Thank you for your interest in contributing to CodeTruth! This document provides guidelines for making contributions.

## Code of Conduct

Be respectful, constructive, and collaborative. Harassment, spam, and toxic behavior will not be tolerated.

## How to Contribute

### 1. Reporting Issues

- Search existing issues before creating a new one
- Use the issue template if available
- Include: steps to reproduce, expected vs actual behavior, environment details
- For security issues, email maintainers directly instead of public issues

### 2. Feature Requests

- Describe the problem your feature solves
- Explain how it fits into CodeTruth's mission
- Include example use cases
- Be open to discussion about implementation

### 3. Pull Requests

1. **Fork** the repository
2. **Create a branch**: `git checkout -b feature/your-feature-name`
3. **Make changes**: Follow coding standards below
4. **Add tests**: All new features must include tests
5. **Update docs**: If you change APIs, update documentation
6. **Run checks**: `pytest`, `ruff`, `mypy`
7. **Commit**: Use clear, descriptive commit messages
8. **Push and create PR**: Describe what you changed and why

### PR Requirements

- [ ] All tests pass (`pytest`)
- [ ] Code formatted (`black .`)
- [ ] Linting passes (`ruff check .`)
- [ ] Type checking passes (`mypy codetruth/`)
- [ ] New code has tests
- [ ] Documentation updated
- [ ] No breaking changes without discussion

## Development Setup

```bash
# Clone
git clone https://github.com/lanekingkong/codetruth.git
cd codetruth

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Check code quality
ruff check codetruth/ tests/
mypy codetruth/
```

## Coding Standards

### Python Style

- **Formatting**: Black (line length 120)
- **Linting**: Ruff (replaces flake8, isort, pyflakes)
- **Type hints**: Required for all public APIs
- **Docstrings**: Google-style for functions and classes
- **Imports**: Standard library → third-party → local; sorted alphabetically

### Naming Conventions

- `snake_case` for functions, variables, modules
- `PascalCase` for classes
- `UPPER_CASE` for constants
- Private members prefixed with `_`

### Testing Guidelines

- Use `pytest` with fixtures
- One test file per module
- Test the public API primarily
- Include edge cases and error paths
- Aim for >80% coverage on new code

## Project Structure Conventions

```
codetruth/
├── __init__.py          # Package metadata
├── config/              # Configuration (settings.py)
├── engine/              # Core engines
│   ├── provenance/      # One engine per sub-package
│   ├── graph/
│   ├── scoring/
│   └── optimizer/
├── memory/              # Memory layer
├── gates/               # Quality gates
├── cli/                 # CLI commands
├── api/                 # FastAPI app
└── web/                 # Web dashboard

tests/
├── conftest.py          # Shared fixtures
├── unit/                # Unit tests
└── integration/         # Integration tests
```

## Release Process

1. Update version in `codetruth/__init__.py`
2. Update CHANGELOG.md
3. Create a git tag: `git tag v1.x.x`
4. Push tag: `git push origin v1.x.x`
5. GitHub Actions will build and publish to PyPI

## Getting Help

- Check existing documentation: `README.md`, `ARCHITECTURE.md`
- Open a GitHub Discussion for questions
- Tag maintainers for urgent issues

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for helping make AI-generated code more trustworthy!