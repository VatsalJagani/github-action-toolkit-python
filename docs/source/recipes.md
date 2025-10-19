# Recipes and Patterns

Common patterns and best practices for building GitHub Actions with github-action-toolkit.

## Table of Contents

- [Input Validation](#input-validation)
- [Output Patterns](#output-patterns)
- [Grouping and Organization](#grouping-and-organization)
- [Annotations](#annotations)
- [Job Summary Templates](#job-summary-templates)
- [Error Handling](#error-handling)
- [Caching Strategies](#caching-strategies)
- [Artifact Patterns](#artifact-patterns)
- [API Rate Limiting](#api-rate-limiting)
- [Testing Actions](#testing-actions)

## Input Validation

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

## Output Patterns

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

## Grouping and Organization

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

## Annotations

### File Annotations

```python
from github_action_toolkit import error, warning, notice

# Error in specific file and line
error(
    'Undefined variable "x"',
    file='src/main.py',
    line=42,
    col=10,
    title='Python Error'
)

# Warning with line range
warning(
    'Function too complex (cyclomatic complexity: 15)',
    file='src/utils.py',
    line=100,
    end_line=150,
    title='Code Quality'
)

# Notice with column range
notice(
    'Consider using f-string for better performance',
    file='src/format.py',
    line=23,
    col=5,
    end_column=30,
    title='Optimization Suggestion'
)
```

### Linter Output Parsing

```python
import re
from github_action_toolkit import error, warning

def parse_and_annotate_pylint(output: str):
    """Parse pylint output and create annotations."""
    # Example: src/main.py:42:10: E0602: Undefined variable 'x'
    pattern = r'^(.+?):(\d+):(\d+): ([EWC]\d+): (.+)$'
    
    for line in output.splitlines():
        match = re.match(pattern, line)
        if not match:
            continue
        
        file, line_num, col, code, message = match.groups()
        
        if code.startswith('E'):
            error(message, file=file, line=int(line_num), col=int(col))
        elif code.startswith('W'):
            warning(message, file=file, line=int(line_num), col=int(col))
```

### Test Failure Annotations

```python
from github_action_toolkit import error

def annotate_test_failures(failures: list[dict]):
    """Annotate failed tests with file locations."""
    for failure in failures:
        error(
            f"Test '{failure['test_name']}' failed: {failure['message']}",
            file=failure['file'],
            line=failure['line'],
            title=f"Test Failure: {failure['test_name']}"
        )
```

## Job Summary Templates

### Test Report with Details

```python
from github_action_toolkit import JobSummary

def create_test_summary(results):
    """Create detailed test summary."""
    summary = JobSummary()
    
    # Overall results
    summary.add_heading('Test Results', 1)
    summary.add_table([
        ['Metric', 'Value'],
        ['Total Tests', str(results['total'])],
        ['✓ Passed', str(results['passed'])],
        ['✗ Failed', str(results['failed'])],
        ['⊘ Skipped', str(results['skipped'])],
        ['Duration', results['duration']],
    ])
    
    # Failures (if any)
    if results['failures']:
        summary.add_separator()
        summary.add_heading('Failed Tests', 2)
        for failure in results['failures']:
            summary.add_details(
                f"✗ {failure['name']}",
                f"```\n{failure['traceback']}\n```"
            )
    
    summary.write()
```

### Coverage Report with Colors

```python
from github_action_toolkit import JobSummary

def coverage_badge(percentage: float) -> str:
    """Return emoji badge for coverage level."""
    if percentage >= 90:
        return '🟢'
    elif percentage >= 75:
        return '🟡'
    else:
        return '🔴'

def create_coverage_summary(coverage_data: dict[str, float]):
    """Create coverage report with visual indicators."""
    summary = JobSummary()
    
    summary.add_heading('Code Coverage', 1)
    
    rows = [['File', 'Coverage', 'Status']]
    for file, coverage in sorted(coverage_data.items()):
        badge = coverage_badge(coverage)
        rows.append([file, f'{coverage:.1f}%', badge])
    
    summary.add_table(rows)
    
    # Overall coverage
    overall = sum(coverage_data.values()) / len(coverage_data)
    summary.add_separator()
    summary.add_quote(
        f"Overall Coverage: **{overall:.1f}%** {coverage_badge(overall)}"
    )
    
    summary.write()
```

### Benchmark Comparison

```python
from github_action_toolkit import JobSummary

def create_benchmark_summary(current: dict, baseline: dict):
    """Compare current benchmarks to baseline."""
    summary = JobSummary()
    
    summary.add_heading('Performance Benchmarks', 1)
    
    rows = [['Test', 'Current', 'Baseline', 'Change']]
    for test_name, current_time in current.items():
        baseline_time = baseline.get(test_name, current_time)
        change = ((current_time - baseline_time) / baseline_time) * 100
        
        if abs(change) < 5:
            change_str = f"→ {change:+.1f}%"
        elif change < 0:
            change_str = f"✓ {change:+.1f}%"
        else:
            change_str = f"✗ {change:+.1f}%"
        
        rows.append([
            test_name,
            f'{current_time:.2f}s',
            f'{baseline_time:.2f}s',
            change_str
        ])
    
    summary.add_table(rows)
    summary.write()
```

## Error Handling

### Graceful Degradation

```python
from github_action_toolkit import warning, info, error

def process_with_fallback():
    """Try primary method, fall back to secondary."""
    try:
        result = primary_method()
        info('Used primary method successfully')
        return result
    except Exception as e:
        warning(
            f'Primary method failed: {e}. Trying fallback method.',
            title='Fallback Activated'
        )
        try:
            result = fallback_method()
            info('Fallback method succeeded')
            return result
        except Exception as e2:
            error(f'Both methods failed: {e2}', title='Processing Failed')
            raise
```

### Retry with Backoff

```python
import time
from github_action_toolkit import info, warning

def retry_with_backoff(func, max_attempts=3, base_delay=1):
    """Retry a function with exponential backoff."""
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            
            delay = base_delay * (2 ** attempt)
            warning(
                f'Attempt {attempt + 1} failed: {e}. '
                f'Retrying in {delay}s...',
                title='Retry'
            )
            time.sleep(delay)
```

### Context Information in Errors

```python
from github_action_toolkit import error
from github_action_toolkit.exceptions import GitHubActionError

class ProcessingError(GitHubActionError):
    """Error with context about what was being processed."""
    
    def __init__(self, message: str, file: str, line: int | None = None):
        self.file = file
        self.line = line
        super().__init__(
            f"{message} (in {file}" + 
            (f", line {line}" if line else "") + ")"
        )

# Usage
try:
    process_file('data.json')
except Exception as e:
    raise ProcessingError(
        f"Failed to parse JSON: {e}",
        file='data.json',
        line=42
    )
```

## Caching Strategies

### Dependency Caching

```python
from pathlib import Path
from github_action_toolkit import GitHubCache, info

def cache_dependencies(requirements_file: Path):
    """Cache Python dependencies."""
    cache = GitHubCache()
    
    # Generate cache key from requirements hash
    key = f"python-deps-{hash_file(requirements_file)}"
    restore_keys = ['python-deps-']  # Fallback to any python deps
    
    # Try to restore
    cache_hit = cache.restore_cache(
        paths=['.venv'],
        key=key,
        restore_keys=restore_keys
    )
    
    if cache_hit:
        info(f'Cache hit: {key}')
        return True
    
    info('Cache miss, installing dependencies...')
    # Install dependencies
    install_dependencies()
    
    # Save for next time
    cache.save_cache(paths=['.venv'], key=key)
    return False

def hash_file(path: Path) -> str:
    """Generate hash of file contents."""
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()[:8]
```

### Build Output Caching

```python
from github_action_toolkit import GitHubCache, info

def cache_build_artifacts():
    """Cache build outputs."""
    cache = GitHubCache()
    
    # Include environment in key for cross-OS safety
    import platform
    os_name = platform.system().lower()
    
    key = f'build-{os_name}-{get_git_commit_hash()}'
    
    try:
        if cache.restore_cache(paths=['dist', 'build'], key=key):
            info('Using cached build artifacts')
            return True
    except Exception as e:
        info(f'Cache restore failed: {e}')
    
    return False
```

## Artifact Patterns

### Uploading Test Results

```python
from pathlib import Path
from github_action_toolkit import GitHubArtifacts, info

def upload_test_results(results_dir: Path):
    """Upload all test result files as artifacts."""
    artifacts = GitHubArtifacts()
    
    # Upload with pattern matching
    artifacts.upload_artifact(
        name='test-results',
        paths=[results_dir],
        retention_days=30
    )
    
    info(f'Uploaded test results from {results_dir}')
```

### Downloading from Previous Run

```python
from github_action_toolkit import GitHubArtifacts, info

def download_previous_artifact(artifact_name: str, dest: str):
    """Download artifact from previous workflow run."""
    artifacts = GitHubArtifacts()
    
    # Get latest artifact with this name
    artifact_list = artifacts.get_artifacts(name_pattern=artifact_name)
    
    if not artifact_list:
        info(f'No artifact found: {artifact_name}')
        return None
    
    latest = artifact_list[0]
    artifacts.download_artifact(latest.id, dest)
    info(f'Downloaded {artifact_name} to {dest}')
    return dest
```

### Conditional Artifact Upload

```python
from github_action_toolkit import GitHubArtifacts, get_user_input_as

def upload_artifacts_if_enabled():
    """Only upload artifacts if configured."""
    upload_artifacts = get_user_input_as(
        'upload-artifacts',
        bool,
        default_value=True
    )
    
    if not upload_artifacts:
        info('Artifact upload disabled')
        return
    
    artifacts = GitHubArtifacts()
    artifacts.upload_artifact(
        name='build-output',
        paths=['dist/']
    )
```

## API Rate Limiting

### Automatic Rate Limit Handling

```python
from github_action_toolkit import GitHubAPIClient, info

client = GitHubAPIClient()

# Automatically handles rate limits with retry
with client.with_rate_limit_handling(wait=True):
    repos = client.paginate(lambda: client.github.get_user().get_repos())
    for repo in repos:
        info(f'Processing {repo.full_name}')
        # API calls here are protected
```

### Manual Rate Limit Checking

```python
from github_action_toolkit import GitHubAPIClient, warning
import time

client = GitHubAPIClient()

def check_rate_limit():
    """Check and warn about rate limit."""
    rate_limit = client.get_rate_limit()
    remaining = rate_limit.core.remaining
    
    if remaining < 100:
        reset_time = rate_limit.core.reset.timestamp()
        wait_seconds = reset_time - time.time()
        warning(
            f'Only {remaining} API calls remaining. '
            f'Resets in {wait_seconds/60:.1f} minutes.',
            title='Rate Limit Low'
        )
```

## Testing Actions

### Local Testing with Simulator

```python
from github_action_toolkit import simulate_github_action, SimulatorConfig

def test_greeting_action():
    """Test the greeting action locally."""
    config = SimulatorConfig(
        inputs={'name': 'Test User'},
        repository='testorg/testrepo'
    )
    
    with simulate_github_action(config) as sim:
        # Import and run your action
        from action import main
        main()
    
    # Verify outputs
    assert sim.outputs['greeting'] == 'Hello, Test User!'
    
    # Verify summary was created
    assert 'Greeting' in sim.summary
```

### Integration Testing

```python
import pytest
from github_action_toolkit import simulate_github_action, SimulatorConfig

@pytest.fixture
def github_env():
    """Provide simulated GitHub environment."""
    config = SimulatorConfig(repository='test/repo')
    with simulate_github_action(config) as sim:
        yield sim

def test_action_with_inputs(github_env):
    """Test action with specific inputs."""
    # Your action code runs here
    from action import process_inputs
    result = process_inputs()
    
    assert result is not None
    assert github_env.outputs['status'] == 'success'
```

## Complete Example: Build and Test Action

Here's a complete example combining multiple patterns:

```python
"""
Complete action that builds, tests, and reports results.
"""
from pathlib import Path
from github_action_toolkit import (
    get_user_input,
    get_user_input_as,
    set_output,
    info,
    warning,
    error,
    group,
    JobSummary,
    GitHubCache,
    GitHubArtifacts,
)

def main():
    # Get inputs
    with group('Configuration'):
        python_version = get_user_input('python-version') or '3.11'
        coverage_threshold = get_user_input_as(
            'coverage-threshold',
            float,
            default_value=80.0
        )
        upload_artifacts = get_user_input_as(
            'upload-artifacts',
            bool,
            default_value=True
        )
        info(f'Python version: {python_version}')
        info(f'Coverage threshold: {coverage_threshold}%')
    
    # Try cache
    with group('Cache'):
        cache = GitHubCache()
        cache_hit = cache.restore_cache(
            paths=['.venv'],
            key=f'deps-{python_version}'
        )
        if not cache_hit:
            info('Installing dependencies...')
            # Install logic here
            cache.save_cache(paths=['.venv'], key=f'deps-{python_version}')
    
    # Build
    with group('Build'):
        try:
            # Build logic here
            info('Build successful')
            set_output('build-status', 'success')
        except Exception as e:
            error(f'Build failed: {e}', title='Build Error')
            set_output('build-status', 'failure')
            return 1
    
    # Test
    with group('Test'):
        results = run_tests()  # Your test logic
        set_output('tests-passed', str(results['passed']))
        set_output('tests-failed', str(results['failed']))
    
    # Create summary
    summary = JobSummary()
    summary.add_heading('Build & Test Results', 1)
    summary.add_table([
        ['Metric', 'Value'],
        ['Build Status', '✓ Success'],
        ['Tests Passed', str(results['passed'])],
        ['Tests Failed', str(results['failed'])],
        ['Coverage', f"{results['coverage']:.1f}%"],
    ])
    
    if results['coverage'] < coverage_threshold:
        warning(
            f"Coverage {results['coverage']:.1f}% is below "
            f"threshold {coverage_threshold}%",
            title='Low Coverage'
        )
        summary.add_quote(
            f"⚠️ Coverage below threshold: "
            f"{results['coverage']:.1f}% < {coverage_threshold}%"
        )
    
    summary.write()
    
    # Upload artifacts
    if upload_artifacts:
        with group('Artifacts'):
            artifacts = GitHubArtifacts()
            artifacts.upload_artifact(
                name='test-results',
                paths=['test-results/'],
                retention_days=30
            )
            info('Uploaded test results')
    
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
```

## More Resources

- {doc}`/quickstart` - Get started quickly
- {doc}`/migration` - Migrate from Node.js toolkit
- {doc}`/examples` - More complete examples
- {doc}`/usage/input_output` - Detailed input/output reference
- {doc}`/usage/job_summary` - Job summary reference
