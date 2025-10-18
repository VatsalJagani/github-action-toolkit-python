# Release Automation and Repository Hygiene Improvements

This document summarizes the improvements made to the repository's packaging, release automation, and development workflow.

## Overview

The following improvements have been implemented to modernize the repository and follow Python packaging best practices:

1. **Pre-commit Hooks**: Automated code quality checks before commits
2. **Conventional Commits**: Structured commit messages for automated changelog generation
3. **Granular Optional Extras**: Organized dependencies into focused groups
4. **Enhanced Metadata**: Improved package classifiers for better discoverability
5. **CI/CD Enhancements**: Added type checking, package validation, and commit message validation

## What's New

### Pre-commit Hooks

Pre-commit hooks are now available to automatically check code quality before commits:

```bash
# Install pre-commit hooks
make pre-commit-install

# Run hooks manually on all files
make pre-commit-run
```

The hooks include:
- **Ruff**: Linting and formatting
- **Codespell**: Spell checking
- **Standard checks**: Trailing whitespace, YAML syntax, etc.

### Conventional Commits

The project now follows [Conventional Commits](https://www.conventionalcommits.org/) for structured commit messages:

```
feat: add new feature
fix: correct bug in existing feature
docs: update documentation
chore: update dependencies
```

You can use commitizen to help format commits:
```bash
uv sync --extra commits
uv run cz commit
```

### Granular Optional Extras

Dependencies are now organized into focused groups:

```bash
# Install only what you need
uv sync --extra test        # Testing tools
uv sync --extra lint        # Linting and formatting
uv sync --extra typing      # Type checking
uv sync --extra docs        # Documentation building
uv sync --extra pre-commit  # Pre-commit hooks
uv sync --extra commits     # Conventional commits tools

# Or install everything
uv sync --all-extras  # Same as --extra dev
```

Available extras:
- `test`: pytest, pytest-cov, pytest-sugar
- `lint`: ruff, codespell
- `typing`: basedpyright, mypy, types-requests
- `docs`: sphinx, furo, myst-parser, and related tools
- `utils`: rich, funlog
- `pre-commit`: pre-commit, pyproject-fmt
- `commits`: commitizen
- `dev`: Meta-extra that installs all of the above

### Enhanced CI/CD

A new workflow has been added for comprehensive validation:

**`.github/workflows/type-check-package.yml`** includes:

1. **Type Checking**: Runs mypy on all source files
2. **Package Validation**: 
   - Builds the package
   - Validates metadata with twine
   - Tests package installation
3. **Commit Message Validation**: Checks PRs for conventional commits format

### Improved Package Metadata

Enhanced Trove classifiers for better package discoverability:
- License: Apache Software License
- Python 3 only
- Topic classifiers for Git, Software Development, and Libraries
- Typing support

## For Contributors

### Quick Start

1. **Install dependencies**:
   ```bash
   uv sync --all-extras
   ```

2. **Install pre-commit hooks**:
   ```bash
   make pre-commit-install
   ```

3. **Make your changes and test**:
   ```bash
   make lint   # Run linting
   make test   # Run tests
   uv build    # Build package
   ```

4. **Use conventional commits**:
   ```bash
   git commit -m "feat: add new feature"
   # or use commitizen
   uv run cz commit
   ```

### Running Type Checks

```bash
# Run basedpyright (default)
uv run basedpyright

# Run mypy
uv run mypy
```

### Building Documentation

```bash
# Live preview
make docs-live

# Build only
make docs-check
```

## For Maintainers

### Release Process

The release process now benefits from conventional commits:

1. Update version in `github_action_toolkit/version.py`
2. Run `make create-release` which:
   - Generates changelog from conventional commits
   - Creates a git tag
   - Triggers CI/CD for publishing

### CI/CD Workflows

Three workflows now run on PRs and pushes:

1. **`test.yml`**: Build, test, lint (Python 3.11, 3.12, 3.13)
2. **`type-check-package.yml`**: Type checking, package validation, commit validation
3. **`changelog_check.yml`**: Ensures CHANGELOG.md is updated

### Automated Changelog

With conventional commits, changelog entries can be automatically generated based on commit types:
- `feat:` → New features
- `fix:` → Bug fixes
- `docs:` → Documentation changes
- `chore:` → Maintenance tasks

## Configuration Files

### `.pre-commit-config.yaml`
Defines pre-commit hooks for code quality

### `pyproject.toml` additions
- `[tool.commitizen]`: Conventional commits configuration
- `[tool.mypy]`: Type checking configuration
- Enhanced classifiers and optional extras

### `Makefile` additions
- `pre-commit-install`: Install pre-commit hooks
- `pre-commit-run`: Run hooks manually

## References

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Pre-commit](https://pre-commit.com/)
- [Development Documentation](devtools/development.md)
- [Contributing Guidelines](.github/CONTRIBUTING.md)
- [Release Documentation](devtools/release.md)
