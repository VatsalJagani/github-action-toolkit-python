# github-action-toolkit - Python Package

This is python library for utility functions and class helpful for custom GitHub actions.


# Available Functions

This section documents all the functions provided by `github-action-toolkit`. The functions in the package should be used inside a workflow run.

**Note:** You can run the commands using python's `subprocess` module by using `use_subprocess` function parameter or `COMMANDS_USE_SUBPROCESS` environment variable.

## Print Functions

### **`echo(message, use_subprocess=False)`**

Prints specified message to the action workflow console.

**example:**

```python
>> from github_action_toolkit import echo

>> echo("Hello World")

# Output:
# Hello World
```

### **`debug(message, use_subprocess=False)`**

Prints colorful debug message to the action workflow console.
GitHub Actions Docs: [debug](https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#setting-a-debug-message)

**example:**

```python
>> from github_action_toolkit import debug

>> debug("Hello World")

# Output:
# ::debug ::Hello World
```

### **`notice(message, title=None, file=None, col=None, end_column=None, line=None, end_line=None, use_subprocess=False)`**

Prints colorful notice message to the action workflow console.
GitHub Actions Docs: [notice](https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#setting-a-notice-message)

**example:**

```python
>> from github_action_toolkit import notice

>> notice(
    "test message",
    title="test title",
    file="abc.py",
    col=1,
    end_column=2,
    line=4,
    end_line=5,
)

# Output:
# ::notice title=test title,file=abc.py,col=1,endColumn=2,line=4,endLine=5::test message=
```

### **`warning(message, title=None, file=None, col=None, end_column=None, line=None, end_line=None, use_subprocess=False)`**

Prints colorful warning message to the action workflow console.
GitHub Actions Docs: [warning](https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#setting-a-warning-message)

**example:**

```python
>> from github_action_toolkit import warning

>> warning(
    "test message",
    title="test title",
    file="abc.py",
    col=1,
    end_column=2,
    line=4,
    end_line=5,
)

# Output:
# ::warning title=test title,file=abc.py,col=1,endColumn=2,line=4,endLine=5::test message
```

### **`error(message, title=None, file=None, col=None, end_column=None, line=None, end_line=None, use_subprocess=False)`**

Prints colorful error message to the action workflow console.
GitHub Actions Docs: [error](https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#setting-a-error-message)

**example:**

```python
>> from github_action_toolkit import error

>> error(
    "test message",
    title="test title",
    file="abc.py",
    col=1,
    end_column=2,
    line=4,
    end_line=5,
)

# Output:
# ::error title=test title,file=abc.py,col=1,endColumn=2,line=4,endLine=5::test message
```


### **`add_mask(value, use_subprocess=False)`**

Masking a value prevents a string or variable from being printed in the workflow console.
GitHub Actions Docs: [add_mask](https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#masking-a-value-in-log)

**example:**

```python
>> from github_action_toolkit import add_mask

>> add_mask("test value")

# Output:
# ::add-mask ::test value
```


### **`start_group(title, use_subprocess=False)` and `end_group(use_subprocess=False)`**

Creates an expandable group in the workflow log.
GitHub Actions Docs: [group](https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#grouping-log-lines)

**example:**

```python
>> from github_action_toolkit import echo, start_group, end_group, group

>> start_group("My Group Title")
>> echo("Hello World")
>> end_group()

# Output:
# ::group ::My Group Title
# Hello World
# ::endgroup::

# ====================
# Using Group Context Manager
# ====================

>> with group("My Group Title"):
...   echo("Hello World")

# Output:
# ::group ::My Group Title
# Hello World
# ::endgroup::
```


## Job Summary Functions


### **`append_job_summary(markdown_text)`**

Sets some custom Markdown for each job so that it will be displayed on the summary page of a workflow run.
GitHub Actions Docs: [append_job_summary](https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#adding-a-job-summary)

**example:**

```python
>> from github_action_utils import append_job_summary

>> append_job_summary("# test summary")
```


### **`overwrite_job_summary(markdown_text)`**

Clears all content for the current step, and adds new job summary.
GitHub Actions Docs: [overwrite_job_summary](https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#overwriting-job-summaries)

**example:**

```python
>> from github_action_utils import overwrite_job_summary

>> overwrite_job_summary("# test summary")
```

### **`remove_job_summary()`**

completely removes job summary for the current step.
GitHub Actions Docs: [remove_job_summary](https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#removing-job-summaries)

**example:**

```python
>> from github_action_utils import remove_job_summary

>> remove_job_summary()
```


## Input, Output, Environment Variables & States

### **`get_workflow_environment_variables()`**

Gets all environment variables from the `GITHUB_ENV` environment file which is available to the workflow.
GitHub Actions Docs: [set_env](https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#setting-an-environment-variable)

**example:**

```python
>> from github_action_utils import get_workflow_environment_variables

>> get_workflow_environment_variables()

# Output:
# {"my_env": "test value"}
```

### **`get_env(name)`**

Gets all environment variables from `os.environ` or the `GITHUB_ENV` environment file which is available to the workflow.
This can also be used to get [environment variables set by GitHub Actions](https://docs.github.com/en/actions/learn-github-actions/environment-variables#default-environment-variables).
GitHub Actions Docs: [set_env](https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#setting-an-environment-variable)

**example:**

```python
>> from github_action_utils import get_env

>> get_env("my_env")
>> get_env("GITHUB_API_URL")

# Output:
# test value
# https://api.github.com
```

### **`set_env(name, value)`**

Creates an environment variable by writing this to the `GITHUB_ENV` environment file which is available to any subsequent steps in a workflow job.
GitHub Actions Docs: [set_env](https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#setting-an-environment-variable)

**example:**

```python
>> from github_action_utils import set_env

>> set_env("my_env", "test value")
```

### **`get_user_input(name)`**

Gets user input from running workflow.

**example:**

```python
>> from github_action_toolkit import get_user_input

>> get_user_input("my_input")

# Output:
# my value
```

### **`set_output(name, value)`**

Sets a step's output parameter by writing to `GITHUB_OUTPUT` environment file. Note that the step will need an `id` to be defined to later retrieve the output value.
GitHub Actions Docs: [set_output](https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#setting-an-output-parameter)

**example:**

```python
>> from github_action_toolkit import set_output

>> set_output("my_output", "test value")
```

### **`get_state(name)`**

Gets state environment variable from running workflow.

**example:**

```python
>> from github_action_toolkit import get_state

>> get_state("test_name")

# Output:
# test_value
```

### **`save_state(name, value)`**

Creates an environment variable by writing this to the `GITHUB_STATE` environment file which is available to workflow's pre: or post: actions.
GitHub Actions Docs: [save_state](https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#sending-values-to-the-pre-and-post-actions)

**example:**

```python
>> from github_action_toolkit import save_state

>> save_state("my_state", "test value")
```


## GitHub Action Event Payload


### **`event_payload()`**

Get GitHub Event payload that triggered the workflow.

More details: [GitHub Actions Event Payload](https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads)

**example:**

```python
>> from github_action_utils import event_payload

>> event_payload()

# Output:
# {"action": "opened", "number": 1, "pull_request": {"url": "https://api.github.com/repos/octocat/Hello-World/pulls/1"}, "repository": {"url": "https://api.github.com/repos/octocat/Hello-World"}, "sender": {"login": "octocat"}...}
```
