# Example Workflows

Complete examples of GitHub Actions built with github-action-toolkit.

## Table of Contents

- [Simple Greeter Action](#simple-greeter-action)
- [Code Linter Action](#code-linter-action)
- [Test Reporter Action](#test-reporter-action)
- [Deployment Action](#deployment-action)
- [Multi-Step Pipeline](#multi-step-pipeline)
- [Conditional Execution](#conditional-execution)

## Simple Greeter Action

A basic action that greets users and demonstrates input/output handling.

### action.py

```python
"""Simple greeting action."""
from github_action_toolkit import (
    get_user_input,
    set_output,
    info,
    notice,
    JobSummary,
)

def main():
    # Get input
    name = get_user_input('name') or 'World'
    greeting_type = get_user_input('greeting') or 'Hello'
    
    # Create greeting
    greeting = f"{greeting_type}, {name}!"
    
    # Output to console
    info(f"Creating greeting for {name}...")
    notice(greeting, title='Greeting Created')
    
    # Set output for other steps
    set_output('greeting', greeting)
    set_output('name', name)
    
    # Create job summary
    summary = JobSummary()
    summary.add_heading('Greeting Action', 1)
    summary.add_quote(greeting)
    summary.add_raw(f'\nGreeted: **{name}**')
    summary.write()
    
    info('Action completed successfully!')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
```

### action.yml

```yaml
name: 'Greeter'
description: 'Greets someone'
inputs:
  name:
    description: 'Who to greet'
    required: false
    default: 'World'
  greeting:
    description: 'Type of greeting'
    required: false
    default: 'Hello'
outputs:
  greeting:
    description: 'The full greeting message'
  name:
    description: 'The name that was greeted'
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

### Workflow Usage

```yaml
name: Test Greeter
on: [push]

jobs:
  greet:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Greet
        id: greet
        uses: ./
        with:
          name: 'GitHub'
          greeting: 'Hello'
      
      - name: Show greeting
        run: echo "${{ steps.greet.outputs.greeting }}"
```

## Code Linter Action

An action that runs a linter and creates annotations for issues found.

### action.py

```python
"""Python code linter action."""
import subprocess
import re
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
)

def run_linter(path: str) -> tuple[int, str]:
    """Run pylint and capture output."""
    result = subprocess.run(
        ['pylint', path],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout

def parse_pylint_output(output: str) -> list[dict]:
    """Parse pylint output into structured data."""
    issues = []
    pattern = r'^(.+?):(\d+):(\d+): ([EWC]\d+): (.+)$'
    
    for line in output.splitlines():
        match = re.match(pattern, line)
        if not match:
            continue
        
        file, line_num, col, code, message = match.groups()
        issues.append({
            'file': file,
            'line': int(line_num),
            'col': int(col),
            'code': code,
            'message': message,
            'severity': 'error' if code.startswith('E') else 'warning'
        })
    
    return issues

def create_annotations(issues: list[dict]):
    """Create GitHub annotations for issues."""
    for issue in issues:
        func = error if issue['severity'] == 'error' else warning
        func(
            issue['message'],
            file=issue['file'],
            line=issue['line'],
            col=issue['col'],
            title=f"Lint {issue['code']}"
        )

def create_summary(issues: list[dict]):
    """Create job summary with lint results."""
    summary = JobSummary()
    summary.add_heading('Lint Results', 1)
    
    errors = [i for i in issues if i['severity'] == 'error']
    warnings = [i for i in issues if i['severity'] == 'warning']
    
    # Summary table
    summary.add_table([
        ['Severity', 'Count'],
        ['Errors', str(len(errors))],
        ['Warnings', str(len(warnings))],
        ['Total', str(len(issues))],
    ])
    
    # Details
    if errors:
        summary.add_separator()
        summary.add_heading('Errors', 2)
        for err in errors[:10]:  # Show first 10
            summary.add_raw(
                f"- **{err['file']}:{err['line']}** - {err['message']}\n"
            )
        if len(errors) > 10:
            summary.add_raw(f"\n*...and {len(errors) - 10} more errors*\n")
    
    summary.write()

def main():
    # Get inputs
    path = get_user_input('path') or '.'
    fail_on_error = get_user_input_as('fail-on-error', bool, default_value=True)
    
    info(f'Linting path: {path}')
    
    # Run linter
    with group('Running Pylint'):
        returncode, output = run_linter(path)
        info(f'Pylint finished with code {returncode}')
    
    # Parse results
    with group('Processing Results'):
        issues = parse_pylint_output(output)
        info(f'Found {len(issues)} issues')
        
        # Create annotations
        create_annotations(issues)
        
        # Create summary
        create_summary(issues)
    
    # Set outputs
    errors = sum(1 for i in issues if i['severity'] == 'error')
    warnings = sum(1 for i in issues if i['severity'] == 'warning')
    
    set_output('errors', str(errors))
    set_output('warnings', str(warnings))
    set_output('total-issues', str(len(issues)))
    
    # Fail if configured
    if fail_on_error and errors > 0:
        error(f'Linting failed with {errors} errors', title='Lint Failed')
        return 1
    
    info('Linting complete!')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
```

### action.yml

```yaml
name: 'Python Linter'
description: 'Lint Python code and create annotations'
inputs:
  path:
    description: 'Path to lint'
    required: false
    default: '.'
  fail-on-error:
    description: 'Fail the action if errors are found'
    required: false
    default: 'true'
outputs:
  errors:
    description: 'Number of errors found'
  warnings:
    description: 'Number of warnings found'
  total-issues:
    description: 'Total issues found'
runs:
  using: 'composite'
  steps:
    - uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - run: pip install pylint github-action-toolkit
      shell: bash
    
    - run: python ${{ github.action_path }}/action.py
      shell: bash
```

## Test Reporter Action

Reports test results with rich formatting and annotations.

### action.py

```python
"""Test reporter action."""
import json
from pathlib import Path
from github_action_toolkit import (
    get_user_input,
    get_user_input_as,
    set_output,
    info,
    error,
    group,
    JobSummary,
    JobSummaryTemplate,
    GitHubArtifacts,
)

def load_test_results(file_path: str) -> dict:
    """Load test results from JSON file."""
    return json.loads(Path(file_path).read_text())

def create_annotations(failures: list[dict]):
    """Create annotations for test failures."""
    for failure in failures:
        error(
            failure['message'],
            file=failure['file'],
            line=failure['line'],
            title=f"Test Failed: {failure['name']}"
        )

def main():
    # Get inputs
    results_file = get_user_input('results-file') or 'test-results.json'
    upload_artifacts = get_user_input_as('upload-artifacts', bool, default_value=True)
    
    info(f'Loading test results from {results_file}')
    
    # Load results
    with group('Loading Results'):
        results = load_test_results(results_file)
        info(f"Tests: {results['total']}, "
             f"Passed: {results['passed']}, "
             f"Failed: {results['failed']}")
    
    # Create annotations for failures
    if results['failures']:
        with group('Creating Annotations'):
            create_annotations(results['failures'])
    
    # Create summary using template
    with group('Creating Summary'):
        summary = JobSummaryTemplate.test_report(
            title='Test Results',
            passed=results['passed'],
            failed=results['failed'],
            skipped=results.get('skipped', 0),
            duration=results['duration']
        )
        
        # Add failure details
        if results['failures']:
            summary.add_separator()
            summary.add_heading('Failed Tests', 2)
            for failure in results['failures'][:5]:  # First 5
                summary.add_details(
                    f"❌ {failure['name']}",
                    f"```\n{failure['traceback']}\n```"
                )
        
        summary.write()
    
    # Upload artifacts
    if upload_artifacts and Path('htmlcov').exists():
        with group('Uploading Artifacts'):
            artifacts = GitHubArtifacts()
            artifacts.upload_artifact(
                name='test-results',
                paths=['htmlcov/', results_file],
                retention_days=30
            )
            info('Uploaded test results and coverage')
    
    # Set outputs
    set_output('passed', str(results['passed']))
    set_output('failed', str(results['failed']))
    set_output('status', 'success' if results['failed'] == 0 else 'failure')
    
    # Fail if tests failed
    if results['failed'] > 0:
        error(f"{results['failed']} tests failed", title='Tests Failed')
        return 1
    
    info('All tests passed!')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
```

## Deployment Action

Complete deployment workflow with validation and rollback.

### action.py

```python
"""Deployment action with validation."""
from github_action_toolkit import (
    get_user_input,
    get_user_input_as,
    set_output,
    set_env,
    info,
    warning,
    error,
    group,
    JobSummary,
    CancellationHandler,
    EventPayload,
)
from github_action_toolkit.exceptions import CancellationRequested

def validate_inputs() -> dict:
    """Validate deployment inputs."""
    environment = get_user_input('environment')
    if environment not in ['dev', 'staging', 'production']:
        raise ValueError(f"Invalid environment: {environment}")
    
    version = get_user_input('version')
    if not version:
        raise ValueError("version is required")
    
    dry_run = get_user_input_as('dry-run', bool, default_value=False)
    
    return {
        'environment': environment,
        'version': version,
        'dry_run': dry_run,
    }

def deploy(config: dict) -> dict:
    """Run deployment."""
    info(f"Deploying version {config['version']} "
         f"to {config['environment']}")
    
    if config['dry_run']:
        warning('Dry run mode - no actual deployment', title='Dry Run')
        return {'status': 'dry-run', 'url': None}
    
    # Actual deployment logic here
    deploy_url = f"https://{config['environment']}.example.com"
    
    return {
        'status': 'success',
        'url': deploy_url,
    }

def create_deployment_summary(config: dict, result: dict):
    """Create deployment summary."""
    summary = JobSummary()
    summary.add_heading('Deployment Summary', 1)
    
    # Get event info
    event = EventPayload()
    
    summary.add_table([
        ['Item', 'Value'],
        ['Environment', config['environment']],
        ['Version', config['version']],
        ['Status', result['status']],
        ['Deployed By', event.actor],
        ['Commit', event.sha[:8]],
    ])
    
    if result['url']:
        summary.add_separator()
        summary.add_link('View Application', result['url'])
    
    if config['dry_run']:
        summary.add_separator()
        summary.add_quote('⚠️ This was a dry run. No actual deployment occurred.')
    
    summary.write()

def main():
    # Setup cancellation handling
    cancellation = CancellationHandler()
    
    def cleanup():
        warning('Deployment cancelled - running cleanup')
        # Cleanup logic
    
    cancellation.register(cleanup)
    cancellation.enable()
    
    try:
        # Validate inputs
        with group('Validation'):
            config = validate_inputs()
            info('✓ All inputs valid')
        
        # Deploy
        with group('Deployment'):
            result = deploy(config)
            info(f"✓ Deployment {result['status']}")
        
        # Create summary
        with group('Summary'):
            create_deployment_summary(config, result)
        
        # Set outputs
        set_output('status', result['status'])
        if result['url']:
            set_output('url', result['url'])
            set_env('DEPLOY_URL', result['url'])
        
        info('Deployment complete!')
        return 0
        
    except CancellationRequested:
        error('Deployment cancelled', title='Cancelled')
        return 1
    except Exception as e:
        error(f'Deployment failed: {e}', title='Deployment Error')
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
```

## Multi-Step Pipeline

Complex pipeline with multiple stages and caching.

### action.py

```python
"""Multi-stage build and test pipeline."""
from pathlib import Path
from github_action_toolkit import (
    get_user_input_as,
    set_output,
    info,
    error,
    group,
    JobSummary,
    GitHubCache,
    GitHubArtifacts,
)

def stage_setup(cache: GitHubCache) -> bool:
    """Setup stage with caching."""
    with group('Setup'):
        # Try to restore cache
        cache_hit = cache.restore_cache(
            paths=['.venv'],
            key='deps-v1',
        )
        
        if not cache_hit:
            info('Installing dependencies...')
            # Install logic
            cache.save_cache(paths=['.venv'], key='deps-v1')
        else:
            info('✓ Using cached dependencies')
        
        return True

def stage_build() -> bool:
    """Build stage."""
    with group('Build'):
        info('Compiling source...')
        # Build logic
        info('✓ Build successful')
        return True

def stage_test() -> dict:
    """Test stage."""
    with group('Test'):
        info('Running tests...')
        # Test logic
        results = {'passed': 42, 'failed': 0}
        info(f"✓ Tests: {results['passed']} passed")
        return results

def stage_package(artifacts: GitHubArtifacts) -> bool:
    """Package stage."""
    with group('Package'):
        info('Creating distribution packages...')
        # Package logic
        
        # Upload artifacts
        artifacts.upload_artifact(
            name='dist',
            paths=['dist/'],
        )
        info('✓ Package uploaded')
        return True

def create_pipeline_summary(stages: dict):
    """Create summary of all stages."""
    summary = JobSummary()
    summary.add_heading('Pipeline Summary', 1)
    
    # Stage status
    rows = [['Stage', 'Status', 'Duration']]
    for stage_name, stage_data in stages.items():
        status = '✓' if stage_data['success'] else '✗'
        rows.append([
            stage_name.title(),
            status,
            stage_data['duration']
        ])
    
    summary.add_table(rows)
    summary.write()

def main():
    skip_tests = get_user_input_as('skip-tests', bool, default_value=False)
    
    cache = GitHubCache()
    artifacts = GitHubArtifacts()
    
    stages = {}
    
    try:
        # Setup
        stages['setup'] = {
            'success': stage_setup(cache),
            'duration': '1.2s'
        }
        
        # Build
        stages['build'] = {
            'success': stage_build(),
            'duration': '3.5s'
        }
        
        # Test (optional)
        if not skip_tests:
            test_results = stage_test()
            stages['test'] = {
                'success': test_results['failed'] == 0,
                'duration': '8.3s'
            }
            
            if test_results['failed'] > 0:
                error(f"{test_results['failed']} tests failed")
                return 1
        
        # Package
        stages['package'] = {
            'success': stage_package(artifacts),
            'duration': '2.1s'
        }
        
        # Summary
        create_pipeline_summary(stages)
        
        set_output('status', 'success')
        info('✓ Pipeline complete!')
        return 0
        
    except Exception as e:
        error(f'Pipeline failed: {e}', title='Pipeline Error')
        set_output('status', 'failure')
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
```

## Conditional Execution

Action with conditional logic based on event type.

### action.py

```python
"""Conditional action based on event type."""
from github_action_toolkit import (
    info,
    warning,
    group,
    JobSummary,
    EventPayload,
)

def handle_pull_request(event: EventPayload):
    """Handle pull request events."""
    with group('Pull Request Handler'):
        pr_number = event.get_pr_number()
        info(f'Processing PR #{pr_number}')
        
        # PR-specific logic
        info(f'Head ref: {event.head_ref}')
        info(f'Base ref: {event.base_ref}')
        
        changed_files = event.get_changed_files()
        if changed_files:
            info(f'Changed files: {", ".join(changed_files[:5])}')

def handle_push(event: EventPayload):
    """Handle push events."""
    with group('Push Handler'):
        info(f'Processing push to {event.ref}')
        info(f'Commit: {event.sha[:8]}')
        
        # Push-specific logic

def handle_release(event: EventPayload):
    """Handle release events."""
    with group('Release Handler'):
        info('Processing release event')
        
        # Release-specific logic

def main():
    event = EventPayload()
    
    info(f'Event type: {event.event_name}')
    
    # Conditional execution
    if event.is_pr():
        handle_pull_request(event)
    elif event.event_name == 'push':
        handle_push(event)
    elif event.event_name == 'release':
        handle_release(event)
    else:
        warning(
            f"Unsupported event type: {event.event_name}",
            title='Unsupported Event'
        )
        return 1
    
    # Create summary
    summary = JobSummary()
    summary.add_heading('Event Summary', 1)
    summary.add_table([
        ['Property', 'Value'],
        ['Event', event.event_name],
        ['Actor', event.actor],
        ['Repository', event.repository],
        ['Ref', event.ref],
    ])
    summary.write()
    
    info('Action complete!')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
```

## More Examples

For more examples, see:

- [Examples Directory](https://github.com/VatsalJagani/github-action-toolkit-python/tree/main/examples) - Complete working examples
- {doc}`/recipes` - Code patterns and best practices
- {doc}`/quickstart` - Getting started guide
- {doc}`/migration` - Examples of migrated actions

## Contributing Examples

Have a great example? Contribute it!

1. Fork the repository
2. Add your example to the `examples/` directory
3. Document it clearly with comments
4. Submit a pull request

See {doc}`/CONTRIBUTING` for guidelines.
