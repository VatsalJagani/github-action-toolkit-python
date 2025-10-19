# Debugging Utilities

Debug and troubleshoot GitHub Actions workflows with directory inspection tools.

## Overview

The `Debugging` class provides utilities for inspecting the execution environment and troubleshooting file/directory issues in GitHub Actions.

## API Reference

### `Debugging.print_directory_tree(max_level=3)`

Prints directory and file information in tree format. This helps developers troubleshoot file or folder not found issues and understand GitHub Action's directory structure.

**example:**

```python
from github_action_toolkit import Debugging

Debugging.print_directory_tree()

# Output:
# > Group - DEBUG: Printing Directory Structure. CWD="/root/github-action-toolkit-python"
# github-action-toolkit-python/
# ├── .coverage
# ├── .gitignore
# ├── .readthedocs.yaml
# ├── AGENTS.md
# ├── CHANGELOG.md
# ├── CLAUDE.md
# ├── LICENSE
# ├── Makefile
# ├── README.md
# ├── coverage.xml
# ├── pyproject.toml
# ├── uv.lock
# ├── .cursor/
# │   └── rules/
# │   │   ├── general.mdc
# │   │   └── python.mdc
# ├── tests/
# │   ├── .coveragerc
# │   ├── __init__.py
# │   ├── test_event_payload.py
# │   ├── test_git_manager.py
# │   ├── test_github_artifacts.py
# │   ├── test_input_output.py
# │   ├── test_job_summary.py
# │   ├── test_print_messages.py

Debugging.print_directory_tree(max_level=1)

# Output:
# > Group - DEBUG: Printing Directory Structure. CWD="/root/github-action-toolkit-python"
# github-action-toolkit-python/
# ├── .coverage
# ├── .gitignore
# ├── .readthedocs.yaml
# ├── AGENTS.md
# ├── CHANGELOG.md
# ├── CLAUDE.md
# ├── LICENSE
# ├── Makefile
# ├── README.md
# ├── coverage.xml
# ├── pyproject.toml
# ├── uv.lock
# ├── .cursor/
# ├── tests/
```
