# Print Functions

Output messages to the GitHub Actions console with different severity levels.

## API Reference

### `echo(message, use_subprocess=False)`

Prints specified message to the action workflow console.

**example:**

```python
>> from github_action_toolkit import echo

>> echo("Hello World")

# Output:
# Hello World
```

### `info(message, use_subprocess=False)`

Prints specified message to the action workflow console. (Same function as `echo()`)

**example:**

```python
>> from github_action_toolkit import info

>> info("Hello World-1")

# Output:
# Hello World-1
```

### `debug(message, use_subprocess=False)`

Prints colorful debug message to the action workflow console.
GitHub Actions Docs: [debug](https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#setting-a-debug-message)

**example:**

```python
>> from github_action_toolkit import debug

>> debug("Hello World")

# Output:
# ::debug ::Hello World
```

### `notice(message, title=None, file=None, col=None, end_column=None, line=None, end_line=None, use_subprocess=False)`

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

### `warning(message, title=None, file=None, col=None, end_column=None, line=None, end_line=None, use_subprocess=False)`

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

### `error(message, title=None, file=None, col=None, end_column=None, line=None, end_line=None, use_subprocess=False)`

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


### `add_mask(value, use_subprocess=False)`

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


## Examples and Best Practices

### Progress Groups

```python
from github_action_toolkit import group, info

stages = ['setup', 'build', 'test', 'deploy']

for stage in stages:
    with group(f'Stage: {stage}'):
        info(f'Starting {stage}...')
        # Do work
        info(f'Completed {stage}')
```

### Nested Groups

```python
from github_action_toolkit import group, info

with group('Build Process'):
    info('Starting build...')
    
    with group('Compile Source'):
        info('Compiling main.py...')
        info('Compiling utils.py...')
    
    with group('Run Tests'):
        info('Running unit tests...')
        info('Running integration tests...')
    
    info('Build complete!')
```

### Conditional Groups

```python
from github_action_toolkit import group, info, get_user_input_as

verbose = get_user_input_as('verbose', bool, default_value=False)

if verbose:
    with group('Detailed Information'):
        info('Python version: 3.11')
        info('Platform: Linux')
        info('Working directory: /home/runner/work')
```
