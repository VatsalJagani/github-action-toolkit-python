# Action Outputs

Set outputs and manage PATH for subsequent workflow steps.

## API Reference

### `set_output(name, value)`

Sets a step's output parameter by writing to `GITHUB_OUTPUT` environment file. Note that the step will need an `id` to be defined to later retrieve the output value.
GitHub Actions Docs: [set_output](https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#setting-an-output-parameter)

**example:**

```python
>> from github_action_toolkit import set_output

>> set_output("my_output", "test value")
```

### `add_path(path)`

Prepends a directory to the system PATH for all subsequent actions in the current job. The newly added path is available in the current action and all subsequent actions.

**example:**

```python
>> from github_action_toolkit import add_path
>> from pathlib import Path

>> # Add using string path
>> add_path("/usr/local/bin")

>> # Add using pathlib.Path
>> add_path(Path("/opt/custom-tools/bin"))
```

**Note:** The path must be an absolute path. Relative paths will raise a `ValueError`.


## Examples and Best Practices

### Structured JSON Output

```python
import json
from github_action_toolkit import set_output

results = {
    'status': 'success',
    'tests_run': 42,
    'tests_passed': 40,
    'tests_failed': 2,
}

# Set as JSON string
set_output('results', json.dumps(results))

# Access in workflow:
# ${{ fromJSON(steps.test.outputs.results).status }}
```

### Multiple Related Outputs

```python
from github_action_toolkit import set_output

def publish_results(results):
    """Publish test results as multiple outputs."""
    set_output('total', str(results['total']))
    set_output('passed', str(results['passed']))
    set_output('failed', str(results['failed']))
    set_output('status', 'success' if results['failed'] == 0 else 'failure')
    set_output('coverage', f"{results['coverage']:.1f}%")

# Usage in workflow:
# ${{ steps.test.outputs.status }}
# ${{ steps.test.outputs.coverage }}
```

### File Path Outputs

```python
from pathlib import Path
from github_action_toolkit import set_output

# Always use absolute paths for outputs
report_path = Path('reports/coverage.html').resolve()
set_output('report-path', str(report_path))
```
