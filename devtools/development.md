# Development

## Setting Up uv

This project is set up to use [uv](https://docs.astral.sh/uv/) to manage Python and
dependencies. First, be sure you
[have uv installed](https://docs.astral.sh/uv/getting-started/installation/).

Then [fork the VatsalJagani/github-action-toolkit
repo](https://github.com/VatsalJagani/github-action-toolkit/fork) (having your own
fork will make it easier to contribute) and
[clone it](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository).


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

# Run uv sync, lint, and test, docs-check:
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
- `dev`: All development dependencies (meta-extra)
- `release`: Release related dependencies (pip, twine)

Install specific extras:
```shell
uv sync --extra test --extra lint
# Or install all at once:
uv sync --all-extras
```


## Agent Rules

This project includes instructions for AI coding assistants. The source rules are located under `.github/copilot-instructions.md`.

But we have a soft-link of instructions/rules for different AI tools:

- **Claude**: `CLAUDE.md` (root) 
- **GitHub Copilot**: `.github/copilot-instructions.md`
- **Other agents**: `AGENTS.md` (root)


## IDE setup

If you use VSCode or a fork like Cursor or Windsurf, you can install the following
extensions:

- [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)

- [Based Pyright](https://marketplace.visualstudio.com/items?itemName=detachhead.basedpyright)
  for type checking. Note that this extension works with non-Microsoft VSCode forks like
  Cursor.
