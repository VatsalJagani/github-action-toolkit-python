# github-action-toolkit - Python Package

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
    get_user_input_as,
    set_output,
    info,
    notice,
    JobSummary,
)

# Type-safe input handling
name = get_user_input('name') or 'World'
timeout = get_user_input_as('timeout', int, default_value=30)

# Rich console output
info(f'Processing for {name}...')
notice(f'Hello, {name}!', title='Greeting')

# Set outputs for other steps
set_output('greeting', f'Hello, {name}!')

# Create formatted job summary
summary = JobSummary()
summary.add_heading('Execution Summary', 1)
summary.add_table([
    ['Parameter', 'Value'],
    ['Name', name],
    ['Timeout', f'{timeout}s'],
])
summary.add_quote('✓ Action completed successfully!')
summary.write()
```

## Installation

Install via pip:

```bash
pip install github-action-toolkit
```

Or with uv:

```bash
uv add github-action-toolkit
```

## Core Capabilities

### Input & Output Management

```python
from github_action_toolkit import (
    get_user_input,
    get_user_input_as,
    set_output,
    set_env,
    with_env,
)

# Get inputs with type conversion
debug = get_user_input_as('debug', bool, default_value=False)
retries = get_user_input_as('retries', int, default_value=3)

# Set outputs for subsequent steps
set_output('result', 'success')

# Manage environment variables
set_env('DEPLOY_URL', 'https://app.example.com')

# Temporary environment variables with automatic cleanup
with with_env(DEBUG='true', LOG_LEVEL='verbose'):
    # Variables are set here
    run_process()
# Variables automatically restored here
```

### Logging & Annotations

```python
from github_action_toolkit import info, warning, error, notice, group

# Structured console output
info('Starting process...')
warning('Resource usage high', title='Performance Warning')
notice('Deployment successful', title='Success')

# File annotations with line/column
error(
    'Undefined variable "x"',
    file='src/main.py',
    line=42,
    col=10,
    title='Syntax Error'
)

# Organized output with collapsible groups
with group('Build Process'):
    info('Compiling source...')
    info('Running tests...')
    info('Build complete!')
```

### Rich Job Summaries

```python
from github_action_toolkit import JobSummary, JobSummaryTemplate

# Use pre-built templates
summary = JobSummaryTemplate.test_report(
    title='Test Results',
    passed=45,
    failed=2,
    skipped=1,
    duration='12.5s'
)

# Or build custom summaries
summary = JobSummary()
summary.add_heading('Deployment Status', 1)
summary.add_table([
    ['Environment', 'Status', 'URL'],
    ['Staging', '✓ Active', 'https://staging.example.com'],
    ['Production', '✓ Active', 'https://app.example.com'],
])
summary.add_separator()
summary.add_code_block('version: 2.5.0\nreleased: 2024-01-15', 'yaml')
summary.write()
```

### GitHub API Integration

```python
from github_action_toolkit import GitHubAPIClient

client = GitHubAPIClient()

# Get repository information
repo = client.get_repository('owner/repo')
print(f'Stars: {repo.stargazers_count}')

# List and paginate
issues = client.paginate(lambda: repo.get_issues(state='open'))
for issue in issues:
    print(f'#{issue.number}: {issue.title}')
```

### Artifacts & Caching

```python
from github_action_toolkit import GitHubArtifacts, GitHubCache

# Upload artifacts
artifacts = GitHubArtifacts()
artifacts.upload_artifact(
    name='test-results',
    paths=['reports/', 'coverage.xml'],
    retention_days=30
)

# Use caching for dependencies
cache = GitHubCache()
cache_hit = cache.restore_cache(
    paths=['.venv'],
    key='python-deps-v1'
)

if not cache_hit:
    # Install dependencies
    install_dependencies()
    cache.save_cache(paths=['.venv'], key='python-deps-v1')
```

### Graceful Cancellation

```python
from github_action_toolkit import CancellationHandler
from github_action_toolkit.exceptions import CancellationRequested

cancellation = CancellationHandler()

def cleanup():
    print('Cleaning up resources...')
    # Cleanup logic here

cancellation.register(cleanup)
cancellation.enable()

try:
    # Long-running operation
    process_data()
except CancellationRequested:
    print('Operation cancelled gracefully')
    raise SystemExit(0)
```

## Documentation

Full documentation is available at: [https://github-action-toolkit.readthedocs.io/](https://github-action-toolkit.readthedocs.io/)

### Quick Links

- [**Quickstart Guide**](https://github-action-toolkit.readthedocs.io/en/latest/quickstart.html) - Get started in minutes
- [**Examples**](https://github-action-toolkit.readthedocs.io/en/latest/examples.html) - Complete workflow examples
- [**API Reference**](https://github-action-toolkit.readthedocs.io/en/latest) - Detailed function documentation

## Comparison with Javascript @actions/toolkit

| Feature | Python | Javascript |
|---------|--------|---------|
| **Syntax** | Clean, readable Python | JavaScript/TypeScript |
| **Type Safety** | Full type hints | TypeScript types |
| **Dependencies** | Simple pip/uv install | npm with bundling |
| **Data Processing** | Rich ecosystem (pandas, numpy) | Limited native support |
| **Learning Curve** | Python (widely known) | JavaScript + Actions API |
| **Local Testing** | Built-in simulator | Manual setup needed |

### Quick Comparison Example

**Before (JavaScript):**
```javascript
const core = require('@actions/core');

const name = core.getInput('name', { required: true });
core.setOutput('greeting', `Hello ${name}`);
core.info('Process complete');
```

**After (Python):**
```python
from github_action_toolkit import get_user_input, set_output, info

name = get_user_input('name')
if not name:
    raise ValueError("name is required")
set_output('greeting', f'Hello {name}')
info('Process complete')
```

## Example Action

Here's a complete example of a Python action:

**action.py:**
```python
from github_action_toolkit import (
    get_user_input,
    get_user_input_as,
    set_output,
    info,
    error,
    JobSummary,
)

def main():
    try:
        # Get inputs
        name = get_user_input('name') or 'World'
        enthusiastic = get_user_input_as('enthusiastic', bool, default_value=False)
        
        # Create greeting
        greeting = f"Hello, {name}{'!' if enthusiastic else '.'}"
        info(greeting)
        
        # Set output
        set_output('greeting', greeting)
        
        # Create summary
        summary = JobSummary()
        summary.add_heading('Greeting Action', 1)
        summary.add_quote(greeting)
        summary.write()
        
        return 0
    except Exception as e:
        error(f'Action failed: {e}', title='Error')
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
```

**action.yml:**
```yaml
name: 'Python Greeter'
description: 'A simple greeting action'
inputs:
  name:
    description: 'Name to greet'
    required: false
    default: 'World'
  enthusiastic:
    description: 'Add enthusiasm'
    required: false
    default: 'false'
outputs:
  greeting:
    description: 'The greeting message'
runs:
  using: 'composite'
  steps:
    - uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    - run: pip install github-action-toolkit
      shell: bash
    - run: python ${{ github.action_path }}/action.py
      shell: bash
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## Project Documentation

For development workflows, see [development.md](devtools/development.md).

For release process, see [release.md](devtools/release.md).
