# Environment Variables

Manage environment variables and state in GitHub Actions workflows.

## API Reference

### `get_workflow_environment_variables()`

Gets all environment variables from the `GITHUB_ENV` environment file which is available to the workflow.
GitHub Actions Docs: [set_env](https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#setting-an-environment-variable)

**example:**

```python
>> from github_action_toolkit import get_workflow_environment_variables

>> get_workflow_environment_variables()

# Output:
# {"my_env": "test value"}
```

### `get_env(name)`

Gets all environment variables from `os.environ` or the `GITHUB_ENV` environment file which is available to the workflow.
This can also be used to get [environment variables set by GitHub Actions](https://docs.github.com/en/actions/learn-github-actions/environment-variables#default-environment-variables).
GitHub Actions Docs: [set_env](https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#setting-an-environment-variable)

**example:**

```python
>> from github_action_toolkit import get_env

>> get_env("my_env")
>> get_env("GITHUB_API_URL")

# Output:
# test value
# https://api.github.com
```

### `set_env(name, value)`

Creates an environment variable by writing this to the `GITHUB_ENV` environment file which is available to any subsequent steps in a workflow job.
GitHub Actions Docs: [set_env](https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#setting-an-environment-variable)

**example:**

```python
>> from github_action_toolkit import set_env

>> set_env("my_env", "test value")
```

### `export_variable(name, value)`

Sets an environment variable for your workflows (alias for `set_env`). This matches the naming convention from the Javascript `@actions/toolkit`.

**example:**

```python
>> from github_action_toolkit import export_variable

>> export_variable("BUILD_NUMBER", "123")
>> export_variable("DEPLOY_ENV", "production")
```

### `with_env(**env_vars)`

Context manager for temporarily setting environment variables. Variables are automatically restored to their original values (or removed if they didn't exist) when the context exits.

**example:**

```python
>> from github_action_toolkit import with_env
>> import os

>> # Temporarily set environment variables
>> with with_env(MY_VAR="value", ANOTHER="test"):
>>     print(os.environ["MY_VAR"])  # "value"
>>     print(os.environ["ANOTHER"])  # "test"
>> # Variables are restored here
>> print(os.environ.get("MY_VAR"))  # None (if it didn't exist before)
```
