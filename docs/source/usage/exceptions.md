Exception Handling
==================

The toolkit provides a comprehensive exception taxonomy for better error handling and debugging. All exceptions inherit from `GitHubActionError`.

## Exception Hierarchy

### **`GitHubActionError`**

Base exception for all github-action-toolkit errors. You can catch this to handle any toolkit-specific error.

**example:**

```python
from github_action_toolkit import GitHubActionError, set_output

try:
    set_output("my_output", "value")
except GitHubActionError as e:
    print(f"Toolkit error: {e}")
```

### **`EnvironmentError`**

Raised when required environment variables are missing or invalid. This typically occurs when the toolkit is not running in a GitHub Actions context or required environment variables are not set.

**example:**

```python
from github_action_toolkit import EnvironmentError, set_output

try:
    set_output("my_output", "value")
except EnvironmentError as e:
    print(f"Missing environment variable: {e}")
    # Error message: "GITHUB_OUTPUT environment variable is not set..."
```

### **`InputError`**

Raised when user input is invalid or cannot be parsed. This occurs when converting input values to specific types fails or when required inputs are missing.

**example:**

```python
from github_action_toolkit import InputError, get_user_input_as

try:
    port = get_user_input_as("port", int)
except InputError as e:
    print(f"Invalid input: {e}")
    # Error message: "Cannot convert input 'port' with value 'abc' to int..."
```

### **`GitOperationError`**

Raised when git operations fail. This occurs during repository operations like clone, checkout, commit, push, etc.

**example:**

```python
from github_action_toolkit import GitOperationError, Repo

try:
    repo = Repo(url="https://invalid-url.com/repo.git")
except GitOperationError as e:
    print(f"Git operation failed: {e}")
```

### **`GitHubAPIError`**

Raised when GitHub API operations fail. This occurs when interacting with GitHub APIs for artifacts, PRs, etc.

**example:**

```python
from github_action_toolkit import GitHubAPIError, GitHubArtifacts

try:
    artifacts = GitHubArtifacts(github_token="invalid_token")
except GitHubAPIError as e:
    print(f"GitHub API error: {e}")
```

### **`ConfigurationError`**

Raised when configuration is invalid or incomplete. This occurs when required configuration parameters are missing or invalid.

**example:**

```python
from github_action_toolkit import ConfigurationError, Repo

try:
    repo = Repo()  # Neither url nor path provided
except ConfigurationError as e:
    print(f"Configuration error: {e}")
    # Error message: "Either 'url' or 'path' must be provided..."
```

## Best Practices

### Catch Specific Exceptions

Catch specific exception types to handle different error scenarios appropriately:

```python
from github_action_toolkit import (
    EnvironmentError,
    InputError,
    ConfigurationError,
    get_user_input_as,
    set_output,
)

try:
    timeout = get_user_input_as("timeout", int, default_value=30)
    set_output("timeout_value", timeout)
except InputError as e:
    print(f"Invalid timeout input: {e}")
    # Provide default or exit
except EnvironmentError as e:
    print(f"Not running in GitHub Actions: {e}")
    # Handle non-GitHub Actions environment
except Exception as e:
    print(f"Unexpected error: {e}")
    raise
```

### Use Error Messages for Debugging

All exceptions provide actionable error messages that explain:
- What went wrong
- Why it went wrong
- How to fix it

```python
from github_action_toolkit import GitHubArtifacts, ConfigurationError

try:
    artifacts = GitHubArtifacts(github_repo="invalid")
except ConfigurationError as e:
    # Error message includes: "github_repo must be in 'owner/repo' format, got 'invalid'"
    # and suggests: "Example: 'octocat/hello-world'"
    print(e)
```
