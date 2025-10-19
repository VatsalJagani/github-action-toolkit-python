# User Inputs

Get and validate user inputs from GitHub Actions workflow configuration.

## API Reference

### `get_all_user_inputs()`

Gets all user inputs from environment variables prefixed with INPUT_, and returns them as a dictionary.

The input names are normalized to lowercase (e.g., INPUT_USERNAME becomes "username").

**example:**

```python
>> from github_action_toolkit import get_all_user_inputs

>> # Assuming these environment variables:
>> # INPUT_USERNAME="alice"
>> # INPUT_DEBUG="true"

>> get_all_user_inputs()

# Output:
# {'username': 'alice', 'debug': 'true'}

```

### `print_all_user_inputs()`

Prints all user inputs (from environment variables prefixed with INPUT_) in a readable format.

If no user inputs are found, it prints a fallback message.

**example:**

```python
>> from github_action_toolkit import print_all_user_inputs

>> # Assuming these environment variables:
>> # INPUT_API_KEY="abc123"
>> # INPUT_VERBOSE="yes"

>> print_all_user_inputs()

# Output:
# User Inputs:
#   api_key: abc123
#   verbose: yes

# Output - If no inputs are found:
# No user inputs found.
```

### `get_user_input(name)`

Gets user input from running workflow.

**example:**

```python
>> from github_action_toolkit import get_user_input

>> get_user_input("my_input")

# Output:
# my value
```

### `get_user_input_as(name, input_type, default_value)`

Gets user input from running workflow with type-casting into choice.

**example:**

```python
>> from github_action_toolkit import get_user_input_as

>> get_user_input_as("my_bool_input", bool, False)

# Output:
# False
```


## Examples and Best Practices

### Required Inputs with Clear Errors

```python
from github_action_toolkit import get_user_input, error
from github_action_toolkit.exceptions import InputError

def get_required_input(name: str, description: str = "") -> str:
    """Get a required input or raise a clear error."""
    value = get_user_input(name)
    if not value:
        msg = f"Input '{name}' is required."
        if description:
            msg += f" {description}"
        error(msg, title="Missing Required Input")
        raise InputError(msg)
    return value

# Usage
api_key = get_required_input(
    'api_key',
    "Set it with 'api_key: ${{ secrets.API_KEY }}'"
)
```

### Input with Choices

```python
from github_action_toolkit import get_user_input, warning

VALID_ENVIRONMENTS = ['dev', 'staging', 'production']

environment = get_user_input('environment') or 'dev'
if environment not in VALID_ENVIRONMENTS:
    warning(
        f"Invalid environment '{environment}'. "
        f"Valid options: {', '.join(VALID_ENVIRONMENTS)}. "
        f"Defaulting to 'dev'.",
        title="Invalid Input"
    )
    environment = 'dev'
```

### Multiple Inputs (Comma-Separated)

```python
from github_action_toolkit import get_user_input

files_input = get_user_input('files') or ''
files = [f.strip() for f in files_input.split(',') if f.strip()]

# Usage in action.yml:
# files: 'src/**/*.py, tests/**/*.py, *.py'
```

### Boolean Flags

```python
from github_action_toolkit import get_user_input_as

# Handles: 'true', 'false', '1', '0', 'yes', 'no'
debug = get_user_input_as('debug', bool, default_value=False)
dry_run = get_user_input_as('dry-run', bool, default_value=False)
```
