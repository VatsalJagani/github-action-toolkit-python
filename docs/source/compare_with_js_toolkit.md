# Comparison with Javascript @actions/toolkit

This guide helps you compare GitHub Action Toolkit in Python compares JavaScript/TypeScript using `@actions/toolkit` with  Python using `github-action-toolkit`.

## Package Mapping

| Javascript Package | Python Equivalent | Notes |
|----------------|------------------|-------|
| `@actions/core` | `github_action_toolkit` | Core functionality |
| `@actions/github` | `github_action_toolkit.GitHubAPIClient` | GitHub API access |
| `@actions/exec` | Python `subprocess` | Command execution |
| `@actions/io` | Python `pathlib`, `shutil` | File operations |
| `@actions/tool-cache` | `github_action_toolkit.GitHubCache` | Caching |
| `@actions/artifact` | `github_action_toolkit.GitHubArtifacts` | Artifacts |

## Function Mapping

### Core Functions (@actions/core)

#### Inputs and Outputs

```javascript
// JavaScript
const core = require('@actions/core');

const name = core.getInput('name', { required: true });
const timeout = parseInt(core.getInput('timeout')) || 30;
core.setOutput('result', 'success');
```

```python
# Python
from github_action_toolkit import get_user_input, get_user_input_as, set_output

name = get_user_input('name')  # Returns None if not set
if not name:
    raise ValueError("name is required")
timeout = get_user_input_as('timeout', int, default_value=30)
set_output('result', 'success')
```

#### Logging

```javascript
// JavaScript
core.info('Information message');
core.debug('Debug message');
core.warning('Warning message');
core.error('Error message');
core.notice('Notice message');
```

```python
# Python
from github_action_toolkit import info, debug, warning, error, notice

info('Information message')
debug('Debug message')
warning('Warning message')
error('Error message')
notice('Notice message')
```

#### Groups

```javascript
// JavaScript
core.startGroup('My group');
console.log('Inside group');
core.endGroup();

// Or with async function
await core.group('My group', async () => {
  console.log('Inside group');
});
```

```python
# Python
from github_action_toolkit import start_group, end_group, group

# Manual start/end
start_group('My group')
print('Inside group')
end_group()

# Or with context manager
with group('My group'):
    print('Inside group')
```

#### Environment Variables

```javascript
// JavaScript
core.exportVariable('MY_VAR', 'value');
const value = process.env.MY_VAR;
```

```python
# Python
from github_action_toolkit import export_variable, get_env

export_variable('MY_VAR', 'value')
value = get_env('MY_VAR')
```

#### Secrets

```javascript
// JavaScript
core.setSecret('my-password');
```

```python
# Python
from github_action_toolkit import add_mask

add_mask('my-password')
```

#### PATH

```javascript
// JavaScript
core.addPath('/usr/local/bin');
```

```python
# Python
from github_action_toolkit import add_path

add_path('/usr/local/bin')
```

#### State

```javascript
// JavaScript
core.saveState('my-state', 'value');
const state = core.getState('my-state');
```

```python
# Python
from github_action_toolkit import save_state, get_state

save_state('my-state', 'value')
state = get_state('my-state')
```

### GitHub API (@actions/github)

```javascript
// JavaScript
const github = require('@actions/github');
const octokit = github.getOctokit(process.env.GITHUB_TOKEN);

const { data: repo } = await octokit.rest.repos.get({
  owner: 'owner',
  repo: 'repo'
});
```

```python
# Python
from github_action_toolkit import GitHubAPIClient

client = GitHubAPIClient()
repo = client.get_repository('owner/repo')
```

### Job Summaries

```javascript
// JavaScript
const core = require('@actions/core');

await core.summary
  .addHeading('Test Results')
  .addTable([
    [{data: 'Test', header: true}, {data: 'Result', header: true}],
    ['test1', '✓ Pass'],
    ['test2', '✓ Pass']
  ])
  .write();
```

```python
# Python
from github_action_toolkit import JobSummary

summary = JobSummary()
summary.add_heading('Test Results', 1)
summary.add_table([
    ['Test', 'Result'],
    ['test1', '✓ Pass'],
    ['test2', '✓ Pass']
])
summary.write()
```

## Workflow File Changes

### Minimal Changes

You can keep most of your workflow structure the same:

```yaml
# Before (JavaScript)
name: My Action
runs:
  using: 'node20'
  main: 'dist/index.js'

# After (Python)
name: My Action
runs:
  using: 'composite'
  steps:
    - name: Run action
      run: python ${{ github.action_path }}/action.py
      shell: bash
```

### Full Comparison

**JavaScript Action:**

```yaml
name: 'JavaScript Action'
description: 'My action in JavaScript'
inputs:
  name:
    description: 'Name to greet'
    required: true
outputs:
  greeting:
    description: 'The greeting'
runs:
  using: 'node20'
  main: 'dist/index.js'
```

**Python Action (Composite):**

```yaml
name: 'Python Action'
description: 'My action in Python'
inputs:
  name:
    description: 'Name to greet'
    required: true
outputs:
  greeting:
    description: 'The greeting'
runs:
  using: 'composite'
  steps:
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: pip install github-action-toolkit
      shell: bash
    
    - name: Run action
      run: python ${{ github.action_path }}/action.py
      shell: bash
```

**Python Action (Docker):**

```yaml
name: 'Python Action'
description: 'My action in Python'
inputs:
  name:
    description: 'Name to greet'
    required: true
outputs:
  greeting:
    description: 'The greeting'
runs:
  using: 'docker'
  image: 'Dockerfile'
```

## Error Handling

### JavaScript

```javascript
// JavaScript
try {
  const result = doSomething();
  core.setOutput('result', result);
} catch (error) {
  core.setFailed(error.message);
}
```

### Python

```python
# Python
from github_action_toolkit import error, set_output

try:
    result = do_something()
    set_output('result', result)
except Exception as e:
    error(str(e), title="Action Failed")
    raise SystemExit(1)
```

## Advanced Patterns

### Async Operations

JavaScript's async/await has Python equivalents:

```javascript
// JavaScript
const results = await Promise.all([
  fetchData1(),
  fetchData2(),
  fetchData3()
]);
```

```python
# Python with asyncio
import asyncio

results = await asyncio.gather(
    fetch_data1(),
    fetch_data2(),
    fetch_data3()
)

# Or with threading for I/O
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor() as executor:
    results = list(executor.map(fetch_data, [1, 2, 3]))
```

### Cancellation Handling

```javascript
// JavaScript
process.on('SIGTERM', () => {
  console.log('Cleaning up...');
  cleanup();
  process.exit(0);
});
```

```python
# Python
from github_action_toolkit import CancellationHandler
from github_action_toolkit.exceptions import CancellationRequested

cancellation = CancellationHandler()

def cleanup():
    print('Cleaning up...')
    # Cleanup code

cancellation.register(cleanup)
cancellation.enable()

try:
    # Your long-running code
    process_data()
except CancellationRequested:
    print('Operation cancelled')
    raise SystemExit(0)
```

## Common Pitfalls

### 1. Input Naming

Node.js / Javascript converts input names automatically:

```javascript
// JavaScript - both work
core.getInput('my-input')
core.getInput('my_input')
```

Python keeps the exact name:

```python
# Python - use exact name from action.yml
get_user_input('my-input')  # if action.yml has 'my-input'
get_user_input('my_input')  # if action.yml has 'my_input'
```

### 2. Boolean Inputs

JavaScript has special boolean handling:

```javascript
// JavaScript
const enabled = core.getBooleanInput('enabled');  // true/false
```

Python requires explicit conversion:

```python
# Python
from github_action_toolkit import get_user_input_as

enabled = get_user_input_as('enabled', bool, default_value=False)
```

### 3. Multiline Outputs

Both support multiline outputs with proper escaping:

```javascript
// JavaScript
core.setOutput('result', 'line1\nline2\nline3');
```

```python
# Python - automatically handles newlines
from github_action_toolkit import set_output

set_output('result', 'line1\nline2\nline3')
```

### 4. Action Metadata

Python actions typically need explicit Python setup in composite actions, while JavaScript actions bundle dependencies:

```yaml
# JavaScript - dependencies bundled in dist/
runs:
  using: 'node20'
  main: 'dist/index.js'

# Python - needs runtime setup
runs:
  using: 'composite'
  steps:
    - uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    - run: pip install github-action-toolkit
      shell: bash
    - run: python action.py
      shell: bash
```

## Benefits of Python

1. **Simpler Dependency Management**: No need for `npm install` or bundling with `ncc`
2. **Better Data Processing**: Rich ecosystem for data manipulation (pandas, numpy, etc.)
3. **Type Safety**: Strong type system with type hints
4. **Familiar Syntax**: Python is widely known and easy to read
5. **Scientific Computing**: Access to ML/AI libraries if needed


## Need Help?

- [GitHub Issues](https://github.com/VatsalJagani/github-action-toolkit-python/issues) - Report migration issues
- [Discussions](https://github.com/VatsalJagani/github-action-toolkit-python/discussions) - Ask questions about migration
