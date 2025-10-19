# Quickstart Guide

Get started with github-action-toolkit in minutes. This guide walks you through building your first GitHub Action in Python.

## Installation

Install the package using pip or uv:

```bash
pip install github-action-toolkit
```

Or with uv:

```bash
uv add github-action-toolkit
```

## Your First Action

Let's create a simple action that greets users and sets an output.

### 1. Create action.py

```python
"""Simple greeting action."""
from github_action_toolkit import (
    get_user_input,
    set_output,
    info,
    notice,
)

# Get input from workflow
name = get_user_input("name") or "World"

# Print messages
info(f"Preparing to greet {name}...")
greeting = f"Hello, {name}!"
notice(greeting, title="Greeting")

# Set output for other steps
set_output("greeting", greeting)
```

### 2. Create action.yml

```yaml
name: 'Python Greeter'
description: 'A simple greeting action in Python'
inputs:
  name:
    description: 'Name to greet'
    required: false
    default: 'World'
outputs:
  greeting:
    description: 'The greeting message'
runs:
  using: 'composite'
  steps:
    - name: Run greeting script
      run: python ${{ github.action_path }}/action.py
      shell: bash
```

### 3. Use in Workflow

```yaml
name: Test Greeting
on: [push]

jobs:
  greet:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install github-action-toolkit
      
      - name: Run greeting
        id: greet
        uses: ./
        with:
          name: 'GitHub Actions'
      
      - name: Use output
        run: echo "${{ steps.greet.outputs.greeting }}"
```

## Common Patterns

### Type-Safe Inputs

Convert inputs to specific types with validation:

```python
from github_action_toolkit import get_user_input_as

# Boolean input
debug = get_user_input_as("debug", bool, default_value=False)

# Integer input
timeout = get_user_input_as("timeout", int, default_value=30)

# List input (comma-separated)
files = get_user_input_as("files", list, default_value=[])
```

### Error Handling

Use structured exceptions for better error messages:

```python
from github_action_toolkit import error, get_user_input
from github_action_toolkit.exceptions import InputError

try:
    api_key = get_user_input("api_key")
    if not api_key:
        raise InputError(
            "api_key is required. "
            "Set it in your workflow with 'api_key: ${{ secrets.API_KEY }}'"
        )
    # Use the API key...
except InputError as e:
    error(str(e), title="Configuration Error")
    raise SystemExit(1)
```

### Grouped Output

Organize console output with collapsible groups:

```python
from github_action_toolkit import group, info

with group("Installing Dependencies"):
    info("Installing package A...")
    info("Installing package B...")
    info("Done!")

with group("Running Tests"):
    info("Running unit tests...")
    info("Running integration tests...")
```

### Job Summaries

Create rich summaries that appear on the workflow run page:

```python
from github_action_toolkit import JobSummary

summary = JobSummary()
summary.add_heading("Test Results", 1)
summary.add_table([
    ["Test Suite", "Status", "Duration"],
    ["Unit Tests", "✓ Passed", "2.5s"],
    ["Integration Tests", "✓ Passed", "5.2s"],
])
summary.write()
```

### Environment Variables

Set environment variables for subsequent steps:

```python
from github_action_toolkit import set_env

# Set for later steps
set_env("DEPLOY_URL", "https://app.example.com")
set_env("BUILD_NUMBER", "42")
```

Temporary environment variables with automatic cleanup:

```python
from github_action_toolkit import with_env
import os

with with_env(DEBUG="true", LOG_LEVEL="verbose"):
    # These variables are set here
    print(os.environ["DEBUG"])  # "true"
# Variables are automatically restored here
```

## Testing Locally

Test your action locally using the simulator:

```python
from github_action_toolkit import simulate_github_action, SimulatorConfig

config = SimulatorConfig(
    repository="myorg/myrepo",
    inputs={"name": "Local Test"},
)

with simulate_github_action(config) as sim:
    # Run your action code
    from action import main
    main()

# Check results
print(sim.outputs)  # {"greeting": "Hello, Local Test!"}
```

## Next Steps

- {doc}`/usage/print_messages` - Master console output and annotations
- {doc}`/usage/input` - Learn about user inputs handling
- {doc}`/usage/output` - Learn about setting outputs
- {doc}`/usage/environment_variables` - Learn about working with environment variables
- {doc}`/usage/job_summary` - Create rich workflow summaries
- {doc}`/compare_with_js_toolkit` - Compare with @actions/toolkit
- {doc}`/examples` - Complete example workflows

## Getting Help

- [GitHub Issues](https://github.com/VatsalJagani/github-action-toolkit-python/issues) - Report bugs or request features
- [Discussions](https://github.com/VatsalJagani/github-action-toolkit-python/discussions) - Ask questions
- [Documentation](https://github-action-toolkit.readthedocs.io/) - Full reference
