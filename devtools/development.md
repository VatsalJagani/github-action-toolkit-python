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



## Agent Rules

This project includes instructions for AI coding assistants. The source rules are in
[.cursor/rules/](.cursor/rules/) directory.

The `make agent-rules` command generates AI assistant instruction files from these source
rules for different AI tools:

- **Cursor**: `.cursorrules` (root) and `.cursor/rules/*.mdc` files
- **Claude**: `CLAUDE.md` (root) 
- **GitHub Copilot**: `.github/copilot-instructions.md`
- **Other agents**: `AGENTS.md` (root)

These generated files are in `.gitignore` and are regenerated as part of `make` default
target. To manually regenerate them:

```shell
make agent-rules
```

### File Locations for Each AI Tool

- **Cursor**: Automatically reads from `.cursorrules` or `.cursor/rules/` directory
- **Claude**: Uses `CLAUDE.md` in the project root
- **GitHub Copilot**: Automatically reads from `.github/copilot-instructions.md`
- **Other agents**: Can use `AGENTS.md` in the project root

All these files contain the same instructions, just in the locations where each tool
expects to find them.

## IDE setup

If you use VSCode or a fork like Cursor or Windsurf, you can install the following
extensions:

- [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)

- [Based Pyright](https://marketplace.visualstudio.com/items?itemName=detachhead.basedpyright)
  for type checking. Note that this extension works with non-Microsoft VSCode forks like
  Cursor.
