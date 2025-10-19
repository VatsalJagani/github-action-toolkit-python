# github-action-toolkit - Python Package

This is python library for utility functions and class helpful for custom GitHub actions.

## Key Features

- ✨ **Type-safe** with full type annotations and modern Python 3.11+ practices
- 🛡️ **Exception taxonomy** with specific exception types for better error handling
- 🔧 **Actionable error messages** that explain what went wrong and how to fix it
- 🎯 **Scoped environment helpers** for temporary environment variables
- 🚦 **Graceful cancellation** support with SIGTERM/SIGINT handlers
- 📚 **Comprehensive documentation** with examples and best practices

## Quick Example

```python
from github_action_toolkit import (
    get_user_input_as,
    with_env,
    enable_cancellation_support,
    CancellationRequested,
)

# Type-safe input handling
timeout = get_user_input_as("timeout", int, default_value=30)

# Scoped environment variables
with with_env(MY_VAR="temporary"):
    # Variable is set here
    pass
# Automatically restored here

# Graceful cancellation
enable_cancellation_support()
try:
    # Your long-running operation
    process_data()
except CancellationRequested:
    print("Cancelled gracefully")
```

## Documentation

Installation & Usage Documentation is hosted at - [https://github-action-toolkit.readthedocs.io/](https://github-action-toolkit.readthedocs.io/)


## Project Docs

For development workflows, see [development.md](devtools/development.md).

For instructions on release process and publishing to PyPI, see [release.md](devtools/release.md).
