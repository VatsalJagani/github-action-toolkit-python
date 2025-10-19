# Examples

This directory contains example code demonstrating the features of `github-action-toolkit`.

## Developer Experience Improvements Demo

**File:** `dx_improvements_demo.py`

This example demonstrates the developer experience improvements including:

- **Exception Handling**: Using specific exception types (`InputError`, `EnvironmentVariableError`, `ConfigurationError`, etc.)
- **Scoped Environment Variables**: Temporary environment variables with `with_env()` context manager
- **Cancellation Support**: Graceful shutdown with SIGTERM/SIGINT handling
- **Actionable Error Messages**: Clear error messages that explain what went wrong and how to fix it

### Running the Example

```bash
# Make sure you have the toolkit installed
pip install github-action-toolkit

# Run the demo
python examples/dx_improvements_demo.py
```

### Example Output

```
Developer Experience Improvements Demo
==================================================
::group ::Exception Handling
=== Exception Handling Demo ===
Timeout set to: 30 seconds
::endgroup::
::group ::Scoped Environment Variables
=== Scoped Environment Demo ===
Before context: MY_TEMP_VAR = not set
Inside context: MY_TEMP_VAR = temporary
Inside context: ANOTHER_VAR = test
After context: MY_TEMP_VAR = not set
Written 3 environment variables to /tmp/tmp2cud__6z.env
::endgroup::
...
```

## Key Features Demonstrated

### 1. Specific Exception Types

Instead of generic exceptions, the toolkit now provides specific exception types:

```python
try:
    timeout = gat.get_user_input_as("timeout", int, default_value=30)
except gat.InputError as e:
    # Handle input errors specifically
    print(f"Invalid input: {e}")
```

### 2. Scoped Environment Variables

Temporarily set environment variables that are automatically restored:

```python
with gat.with_env(MY_VAR="temp", ANOTHER="test"):
    # Variables are set here
    pass
# Variables are restored here
```

### 3. Graceful Cancellation

Handle SIGTERM/SIGINT gracefully with cleanup handlers:

```python
def cleanup():
    print("Cleaning up...")

gat.register_cancellation_handler(cleanup)
gat.enable_cancellation_support()

try:
    long_running_operation()
except gat.CancellationRequested:
    print("Cancelled gracefully")
```

### 4. Actionable Error Messages

All errors include clear explanations:

```
ConfigurationError: Either 'url' or 'path' must be provided.
Provide a Git repository URL to clone or a path to an existing repository.
```

## Contributing Examples

If you have additional examples to contribute, please:

1. Create a new Python file in this directory
2. Add comprehensive comments explaining the code
3. Update this README with a description of your example
4. Test your example to ensure it runs correctly
