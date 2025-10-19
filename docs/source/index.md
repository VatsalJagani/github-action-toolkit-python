# **github-action-toolkit**

A Python library for building powerful GitHub Actions with type safety, rich output formatting, and comprehensive developer tools.

## Key Features

- ✨ **Type-safe** with full type annotations and modern Python 3.11+ practices
- 🛡️ **Exception taxonomy** with specific exception types for better error handling
- 🔧 **Actionable error messages** that explain what went wrong and how to fix it
- 🎯 **Scoped environment helpers** for temporary environment variables
- 🚦 **Graceful cancellation** support with SIGTERM/SIGINT handlers
- 📚 **Comprehensive documentation** with examples and best practices
- 🔒 **Security-focused** with input validation and secrets masking
- 🎨 **Rich job summaries** with tables, code blocks, and templates

## Quick Start

```python
from github_action_toolkit import (
    get_user_input,
    set_output,
    info,
    JobSummary,
)

# Get typed input
name = get_user_input('name') or 'World'

# Print messages
info(f'Hello, {name}!')

# Set outputs
set_output('greeting', f'Hello, {name}!')

# Create rich summary
summary = JobSummary()
summary.add_heading('Results', 1)
summary.add_quote(f'Greeted {name} successfully!')
summary.write()
```

## Documentation

### Quick Reference

Looking for something specific? Here's a quick guide:

**Console Output:**
- {doc}`/usage/print_messages` - Print messages, warnings, errors, and debug information
- {doc}`/usage/file_annotation` - Create file annotations for linting and code review

**Workflow Data:**
- {doc}`/usage/input` - Get user inputs from workflow configuration
- {doc}`/usage/output` - Set outputs and manage PATH
- {doc}`/usage/environment_variables` - Manage environment variables and state

**Job Summaries:**
- {doc}`/usage/job_summary` - Create rich formatted summaries
- {doc}`/usage/job_summary_templates` - Pre-built templates for common use cases

**Error Handling:**
- {doc}`/usage/exceptions` - Exception types and error handling
- {doc}`/usage/signal_handling` - Handle cancellation signals

**GitHub Integration:**
- {doc}`/usage/event_payload` - Access event data from workflow triggers
- {doc}`/usage/git_manager` - Git repository operations
- {doc}`/usage/github_artifacts` - Upload and download artifacts
- {doc}`/usage/github_api_client` - GitHub REST and GraphQL API access
- {doc}`/usage/github_cache` - Cache dependencies and build outputs

**Development:**
- {doc}`/usage/debugging` - Debug and troubleshoot workflows

```{toctree}
:maxdepth: 2
:hidden:
:caption: Getting Started

installation
quickstart
compare_with_js_toolkit
```

```{toctree}
:maxdepth: 2
:hidden:
:caption: Guides

examples
local_development
error_handling
security
```

```{toctree}
:maxdepth: 2
:hidden:
:caption: API Reference and Guide

/usage/print_messages
/usage/file_annotation
/usage/input
/usage/output
/usage/environment_variables
/usage/job_summary
/usage/job_summary_templates
/usage/exceptions
/usage/signal_handling
/usage/event_payload
/usage/git_manager
/usage/github_artifacts
/usage/github_api_client
/usage/github_cache
/usage/debugging
```

```{toctree}
:hidden:
:caption: Development

CHANGELOG
CONTRIBUTING
License <https://raw.githubusercontent.com/VatsalJagani/github-action-toolkit-python/main/LICENSE>
GitHub Repository <https://github.com/VatsalJagani/github-action-toolkit-python>
```

## Why github-action-toolkit?

Building GitHub Actions in Python gives you access to a rich ecosystem of libraries and familiar syntax. This toolkit provides:

- **Simplified API**: Easy-to-use functions that abstract GitHub Actions workflow commands
- **Type Safety**: Full type annotations help catch errors before runtime
- **Better Testing**: Local simulator for testing actions without GitHub
- **Rich Formatting**: Create beautiful job summaries with tables, code blocks, and more
- **Error Handling**: Structured exceptions with actionable error messages
- **Security**: Built-in secrets masking and input validation patterns

## Installation

Install via pip:

```bash
pip install github-action-toolkit
```

Or with uv:

```bash
uv add github-action-toolkit
```

## Common Use Cases

- **Input/Output Handling**: Type-safe input parsing and output setting
- **Logging & Annotations**: Rich console output with file annotations
- **Job Summaries**: Create formatted summaries with tables and charts
- **GitHub API**: Interact with repositories, PRs, and issues
- **Artifacts & Caching**: Manage workflow artifacts and caching
- **Git Operations**: Clone, commit, push, and manage repositories
- **Error Handling**: Structured exceptions with clear error messages

## Getting Help

- {doc}`/quickstart` - Get started in minutes
- {doc}`/compare_with_js_toolkit` - Compare with @actions/toolkit
- {doc}`/examples` - Complete example workflows
- [GitHub Issues](https://github.com/VatsalJagani/github-action-toolkit-python/issues) - Report bugs
- [Discussions](https://github.com/VatsalJagani/github-action-toolkit-python/discussions) - Ask questions


