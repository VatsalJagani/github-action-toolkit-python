Debugging Functions
================

### **`print_directory_tree(max_level: int = 3)`**

Prints directory and file information in tree manner. This will help developer troubleshoot file or folder not found issues and help understand GitHub action's directory structure.

**example:**

```python
>> from github_action_toolkit import print_directory_tree

>> print_directory_tree()

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

>> print_directory_tree(max_level=1)

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
