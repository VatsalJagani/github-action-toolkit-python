# Annotations

Create file annotations and code review comments in GitHub Actions workflows.

## Overview

Annotations allow you to create warnings, errors, and notices that appear in the GitHub Actions UI and pull request files view. They can point to specific files and line numbers, making them perfect for linting, testing, and code quality tools.

## Examples

### File Annotations

```python
from github_action_toolkit import error, warning, notice

# Error in specific file and line
error(
    'Undefined variable "x"',
    file='src/main.py',
    line=42,
    col=10,
    title='Python Error'
)

# Warning with line range
warning(
    'Function too complex (cyclomatic complexity: 15)',
    file='src/utils.py',
    line=100,
    end_line=150,
    title='Code Quality'
)

# Notice with column range
notice(
    'Consider using f-string for better performance',
    file='src/format.py',
    line=23,
    col=5,
    end_column=30,
    title='Optimization Suggestion'
)
```

### Linter Output Parsing

```python
import re
from github_action_toolkit import error, warning

def parse_and_annotate_pylint(output: str):
    """Parse pylint output and create annotations."""
    # Example: src/main.py:42:10: E0602: Undefined variable 'x'
    pattern = r'^(.+?):(\d+):(\d+): ([EWC]\d+): (.+)$'
    
    for line in output.splitlines():
        match = re.match(pattern, line)
        if not match:
            continue
        
        file, line_num, col, code, message = match.groups()
        
        if code.startswith('E'):
            error(message, file=file, line=int(line_num), col=int(col))
        elif code.startswith('W'):
            warning(message, file=file, line=int(line_num), col=int(col))
```

### Test Failure Annotations

```python
from github_action_toolkit import error

def annotate_test_failures(failures: list[dict]):
    """Annotate failed tests with file locations."""
    for failure in failures:
        error(
            f"Test '{failure['test_name']}' failed: {failure['message']}",
            file=failure['file'],
            line=failure['line'],
            title=f"Test Failure: {failure['test_name']}"
        )
```
