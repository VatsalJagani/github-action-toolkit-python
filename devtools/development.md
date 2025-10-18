# Development

## Setting Up uv

This project is set up to use [uv](https://docs.astral.sh/uv/) to manage Python and
dependencies. First, be sure you
[have uv installed](https://docs.astral.sh/uv/getting-started/installation/).

Then [fork the VatsalJagani/github-action-toolkit
repo](https://github.com/VatsalJagani/github-action-toolkit/fork) (having your own
fork will make it easier to contribute) and
[clone it](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository).

## Pre-commit Hooks

This project uses [pre-commit](https://pre-commit.com/) to ensure code quality and consistency.
After cloning the repository, install the pre-commit hooks:

```shell
# Install pre-commit hooks
uv sync --extra pre-commit
uv run pre-commit install

# Run hooks manually on all files
uv run pre-commit run --all-files
```

The pre-commit hooks will automatically:
- Format code with Ruff
- Check for common issues (trailing whitespace, YAML syntax, etc.)
- Run spell checking with codespell
- Format pyproject.toml with pyproject-fmt
- Run type checking with mypy

## Conventional Commits

This project follows [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.
This enables automatic changelog generation and semantic versioning.

Commit message format:
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Common types:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that don't affect code meaning (formatting, etc.)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvement
- `test`: Adding or updating tests
- `chore`: Changes to build process or auxiliary tools

Examples:
```
feat: add support for GitHub artifacts API
fix: correct input validation in get_user_input_as
docs: update README with new examples
chore: update dependencies
```

You can use commitizen to help format commits:
```shell
uv sync --extra commits
uv run cz commit
```

## Basic Developer Workflows

The `Makefile` simply offers shortcuts to `uv` commands for developer convenience.
(For clarity, GitHub Actions don't use the Makefile and just call `uv` directly.)

```shell

# Create virtual environment with uv
uv venv --python 3.11

# Activate virtual environment
source .venv/bin/activate

# This simply runs `uv sync --all-extras` to install all packages,
# including dev dependencies and optional dependencies.
make install

# Run uv sync, lint, and test (and also generate agent rules):
make

# Build wheel:
make build

# Linting:
make lint

# Run tests:
make test

# Delete all the build artifacts:
make clean

# Upgrade dependencies to compatible versions:
make upgrade

# To run tests by hand:
uv run pytest   # all tests
uv run pytest -s github_action_toolkit/some_file.py  # one test, showing outputs

# Build and install current dev executables, to let you use your dev copies
# as local tools:
uv tool install --editable .

# Documentation
# Run Doc locally
make docs-live

# Dependency management directly with uv:
# Add a new dependency:
uv add package_name
# Add a development dependency:
uv add --dev package_name
# Update to latest compatible versions (including dependencies on git repos):
uv sync --upgrade
# Update a specific package:
uv lock --upgrade-package package_name
# Update dependencies on a package:
uv add package_name@latest
```

See [uv docs](https://docs.astral.sh/uv/) for details.

## Optional Dependency Extras

The project provides granular optional dependency groups:

- `test`: Testing dependencies (pytest, pytest-cov, etc.)
- `lint`: Linting and formatting tools (ruff, codespell)
- `typing`: Type checking tools (basedpyright, mypy)
- `docs`: Documentation building tools (sphinx, furo, etc.)
- `utils`: Development utilities (rich, funlog)
- `pre-commit`: Pre-commit hooks and related tools
- `commits`: Conventional commits tools (commitizen)
- `dev`: All development dependencies (meta-extra)

Install specific extras:
```shell
uv sync --extra test --extra lint
# Or install all at once:
uv sync --all-extras
```


## Agent Rules

See [.cursor/rules](.cursor/rules) for agent rules.
These rules are written for [Cursor](https://www.cursor.com/).
However, they are also used by other agents.
The Makefile will generate the following files from the same rules:
- `CLAUDE.md` (for Claude AI)
- `AGENTS.md` (for general agents)
- `.copilot-instructions.md` (for GitHub Copilot)

```shell
make agent-rules
```

## IDE setup

If you use VSCode or a fork like Cursor or Windsurf, you can install the following
extensions:

- [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)

- [Based Pyright](https://marketplace.visualstudio.com/items?itemName=detachhead.basedpyright)
  for type checking. Note that this extension works with non-Microsoft VSCode forks like
  Cursor.
