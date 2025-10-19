# Example Workflows

Complete examples of GitHub Actions built with github-action-toolkit.

## Table of Contents

- [Simple Greeter Action](#simple-greeter-action)
- [Code Linter Action](#code-linter-action)
- [Test Reporter Action](#test-reporter-action)
- [Deployment Action](#deployment-action)
- [Multi-Step Pipeline](#multi-step-pipeline)
- [Conditional Execution](#conditional-execution)
- [Python Test Reporter Action](#python-test-reporter-action)
- [Docker Build and Push Action](#docker-build-and-push-action)

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

## Python Test Reporter Action

Complete test reporting action that runs pytest, parses results, creates annotations, and generates comprehensive job summaries with coverage information.

### test_reporter_action.py

```python
"""
Example: Python Test Reporter Action

This action runs pytest, parses the results, creates annotations for failures,
and generates a comprehensive job summary with coverage information.
"""

import json
import subprocess
from pathlib import Path

from github_action_toolkit import (
    JobSummary,
    error,
    get_user_input_as,
    group,
    info,
    set_output,
    warning,
)


def run_pytest(coverage: bool = True) -> tuple[int, str]:
    """Run pytest with optional coverage."""
    cmd = ['pytest', '--json-report', '--json-report-file=test-report.json']
    if coverage:
        cmd.extend(['--cov', '--cov-report=json'])

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout


def parse_test_results(report_file: Path) -> dict:
    """Parse pytest JSON report."""
    if not report_file.exists():
        return {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'duration': '0s',
            'failures': [],
        }

    data = json.loads(report_file.read_text())

    failures = []
    for test in data.get('tests', []):
        if test['outcome'] == 'failed':
            # Extract file and line from nodeid
            nodeid = test['nodeid']
            if '::' in nodeid:
                file_path = nodeid.split('::')[0]
                failures.append(
                    {
                        'name': test['nodeid'],
                        'message': test.get('call', {}).get('longrepr', 'Test failed'),
                        'file': file_path,
                    }
                )

    return {
        'total': data['summary']['total'],
        'passed': data['summary'].get('passed', 0),
        'failed': data['summary'].get('failed', 0),
        'skipped': data['summary'].get('skipped', 0),
        'duration': f"{data['duration']:.2f}s",
        'failures': failures,
    }


def parse_coverage_report(coverage_file: Path) -> dict[str, float]:
    """Parse coverage.json report."""
    if not coverage_file.exists():
        return {}

    data = json.loads(coverage_file.read_text())
    files_coverage = {}

    for file_path, file_data in data.get('files', {}).items():
        # Calculate coverage percentage
        covered = file_data['summary']['covered_lines']
        total = file_data['summary']['num_statements']
        if total > 0:
            percentage = (covered / total) * 100
            files_coverage[file_path] = percentage

    return files_coverage


def create_test_annotations(failures: list[dict]):
    """Create GitHub annotations for test failures."""
    for failure in failures:
        error(
            failure['message'],
            file=failure.get('file', ''),
            title=f"Test Failed: {failure['name']}",
        )


def coverage_badge(percentage: float) -> str:
    """Return emoji badge for coverage level."""
    if percentage >= 90:
        return '🟢'
    elif percentage >= 75:
        return '🟡'
    else:
        return '🔴'


def create_summary(results: dict, coverage_data: dict[str, float], threshold: float):
    """Create comprehensive job summary."""
    summary = JobSummary()

    # Test Results Header
    summary.add_heading('Test Report', 1)

    # Overall Stats
    summary.add_table(
        [
            ['Metric', 'Value'],
            ['Total Tests', str(results['total'])],
            ['✓ Passed', str(results['passed'])],
            ['✗ Failed', str(results['failed'])],
            ['⊘ Skipped', str(results['skipped'])],
            ['Duration', results['duration']],
        ]
    )

    # Test Failures
    if results['failures']:
        summary.add_separator()
        summary.add_heading('Failed Tests', 2)
        for failure in results['failures'][:10]:  # Show first 10
            summary.add_details(
                f"✗ {failure['name']}",
                f"**File:** {failure['file']}\n\n{failure['message']}",
            )
        if len(results['failures']) > 10:
            summary.add_raw(
                f"\n*...and {len(results['failures']) - 10} more failures*\n"
            )

    # Coverage Report
    if coverage_data:
        summary.add_separator()
        summary.add_heading('Code Coverage', 2)

        # Overall coverage
        overall_coverage = sum(coverage_data.values()) / len(coverage_data)

        rows = [['File', 'Coverage', 'Status']]
        for file, coverage in sorted(coverage_data.items()):
            badge = coverage_badge(coverage)
            rows.append([file, f'{coverage:.1f}%', badge])

        summary.add_table(rows)

        # Coverage threshold check
        if overall_coverage < threshold:
            summary.add_separator()
            summary.add_quote(
                f"⚠️ Coverage ({overall_coverage:.1f}%) is below "
                f"threshold ({threshold}%)"
            )
        else:
            summary.add_separator()
            summary.add_quote(
                f"✓ Coverage ({overall_coverage:.1f}%) meets "
                f"threshold ({threshold}%)"
            )

    summary.write()


def main():
    """Main action entry point."""
    # Get configuration
    coverage_enabled = get_user_input_as('coverage', bool, default_value=True)
    coverage_threshold = get_user_input_as('coverage-threshold', float, default_value=80.0)
    fail_on_error = get_user_input_as('fail-on-error', bool, default_value=True)

    info(f'Running tests with coverage: {coverage_enabled}')
    if coverage_enabled:
        info(f'Coverage threshold: {coverage_threshold}%')

    # Run tests
    with group('Running Tests'):
        returncode, output = run_pytest(coverage=coverage_enabled)
        if returncode == 0:
            info('✓ All tests passed')
        else:
            warning('Some tests failed')

    # Parse results
    with group('Processing Results'):
        results = parse_test_results(Path('test-report.json'))
        info(
            f"Results: {results['passed']} passed, "
            f"{results['failed']} failed, "
            f"{results['skipped']} skipped"
        )

        coverage_data = {}
        if coverage_enabled:
            coverage_data = parse_coverage_report(Path('coverage.json'))
            if coverage_data:
                overall = sum(coverage_data.values()) / len(coverage_data)
                info(f'Overall coverage: {overall:.1f}%')

    # Create annotations
    if results['failures']:
        with group('Creating Annotations'):
            create_test_annotations(results['failures'])

    # Create summary
    with group('Creating Summary'):
        create_summary(results, coverage_data, coverage_threshold)

    # Set outputs
    set_output('total', str(results['total']))
    set_output('passed', str(results['passed']))
    set_output('failed', str(results['failed']))
    set_output('skipped', str(results['skipped']))

    if coverage_data:
        overall = sum(coverage_data.values()) / len(coverage_data)
        set_output('coverage', f'{overall:.1f}')

    # Determine exit code
    if fail_on_error and results['failed'] > 0:
        error(f"{results['failed']} tests failed", title='Tests Failed')
        return 1

    if coverage_data and overall < coverage_threshold:
        error(
            f"Coverage {overall:.1f}% below threshold {coverage_threshold}%",
            title='Coverage Too Low',
        )
        return 1

    info('✓ Tests completed successfully')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
```

## Docker Build and Push Action

Complete Docker workflow that builds images, scans for vulnerabilities, and pushes to container registries with proper tagging and security.

### docker_build_action.py

```python
"""
Example: Docker Build and Push Action

This action builds a Docker image, scans it for vulnerabilities, and pushes it
to a container registry with proper tagging.
"""

import os
import re
import subprocess
from pathlib import Path

from github_action_toolkit import (
    EventPayload,
    JobSummary,
    add_mask,
    error,
    get_user_input,
    get_user_input_as,
    group,
    info,
    set_output,
    warning,
)


def validate_image_name(image: str) -> bool:
    """Validate Docker image name format."""
    pattern = r'^[a-z0-9]+(?:[._-][a-z0-9]+)*(?:/[a-z0-9]+(?:[._-][a-z0-9]+)*)*$'
    return bool(re.match(pattern, image.lower()))


def get_image_tags(event: EventPayload, tag_prefix: str) -> list[str]:
    """Generate appropriate tags based on the event."""
    tags = []

    # Always add commit SHA tag
    tags.append(f'{tag_prefix}:{event.sha[:8]}')

    # Add branch/PR tags
    if event.is_pr():
        pr_number = event.get_pr_number()
        if pr_number:
            tags.append(f'{tag_prefix}:pr-{pr_number}')
    elif event.ref.startswith('refs/heads/'):
        branch = event.ref.replace('refs/heads/', '')
        # Clean branch name for tag
        clean_branch = re.sub(r'[^a-z0-9._-]', '-', branch.lower())
        tags.append(f'{tag_prefix}:{clean_branch}')

        # Add 'latest' for main/master
        if branch in ['main', 'master']:
            tags.append(f'{tag_prefix}:latest')

    return tags


def docker_login(registry: str, username: str, password: str):
    """Login to Docker registry."""
    add_mask(password)  # Mask password from logs

    result = subprocess.run(
        ['docker', 'login', registry, '-u', username, '--password-stdin'],
        input=password.encode(),
        capture_output=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f'Docker login failed: {result.stderr.decode()}')

    info(f'✓ Logged into {registry}')


def docker_build(dockerfile: Path, context: Path, image_tag: str, build_args: dict) -> str:
    """Build Docker image."""
    cmd = ['docker', 'build', '-f', str(dockerfile), '-t', image_tag]

    # Add build args
    for key, value in build_args.items():
        cmd.extend(['--build-arg', f'{key}={value}'])

    cmd.append(str(context))

    info(f'Building image: {image_tag}')
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f'Docker build failed:\n{result.stderr}')

    # Get image ID
    result = subprocess.run(
        ['docker', 'images', '-q', image_tag], capture_output=True, text=True
    )
    image_id = result.stdout.strip()

    info(f'✓ Built image: {image_id[:12]}')
    return image_id


def docker_push(image_tag: str):
    """Push Docker image to registry."""
    info(f'Pushing {image_tag}...')

    result = subprocess.run(['docker', 'push', image_tag], capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f'Docker push failed:\n{result.stderr}')

    info(f'✓ Pushed {image_tag}')


def scan_image(image_tag: str) -> dict:
    """Scan image for vulnerabilities (example using trivy)."""
    info(f'Scanning {image_tag} for vulnerabilities...')

    result = subprocess.run(
        ['trivy', 'image', '--format', 'json', '--quiet', image_tag],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        warning(f'Image scan completed with warnings')
        return {}

    # Parse scan results (simplified)
    # In production, parse the JSON and extract vulnerability counts
    info('✓ Security scan complete')
    return {'critical': 0, 'high': 2, 'medium': 5, 'low': 10}


def create_summary(image: str, tags: list[str], image_id: str, scan_results: dict):
    """Create job summary for the build."""
    summary = JobSummary()

    summary.add_heading('Docker Build Summary', 1)

    # Build info
    summary.add_table(
        [
            ['Property', 'Value'],
            ['Image', image],
            ['Image ID', image_id[:12]],
            ['Tags', str(len(tags))],
        ]
    )

    # Tags
    summary.add_separator()
    summary.add_heading('Image Tags', 2)
    for tag in tags:
        summary.add_raw(f'- `{tag}`\n')

    # Security scan
    if scan_results:
        summary.add_separator()
        summary.add_heading('Security Scan', 2)
        summary.add_table(
            [
                ['Severity', 'Count'],
                ['Critical', str(scan_results.get('critical', 0))],
                ['High', str(scan_results.get('high', 0))],
                ['Medium', str(scan_results.get('medium', 0))],
                ['Low', str(scan_results.get('low', 0))],
            ]
        )

        if scan_results.get('critical', 0) > 0:
            summary.add_separator()
            summary.add_quote('⚠️ Critical vulnerabilities detected!')

    summary.write()


def main():
    """Main action entry point."""
    # Get inputs
    image_name = get_user_input('image-name')
    if not image_name:
        error('image-name is required', title='Missing Input')
        return 1

    if not validate_image_name(image_name):
        error(
            f'Invalid image name: {image_name}. '
            'Must contain only lowercase letters, numbers, and separators.',
            title='Invalid Input',
        )
        return 1

    registry = get_user_input('registry') or 'docker.io'
    dockerfile = Path(get_user_input('dockerfile') or 'Dockerfile')
    context = Path(get_user_input('context') or '.')
    push_enabled = get_user_input_as('push', bool, default_value=True)
    scan_enabled = get_user_input_as('scan', bool, default_value=True)

    # Get credentials (mask them)
    username = get_user_input('username')
    password = get_user_input('password')
    if password:
        add_mask(password)

    # Validate files exist
    if not dockerfile.exists():
        error(f'Dockerfile not found: {dockerfile}', title='File Not Found')
        return 1

    if not context.exists():
        error(f'Build context not found: {context}', title='Directory Not Found')
        return 1

    info(f'Building {image_name} from {dockerfile}')

    # Get event info for tagging
    event = EventPayload()
    full_image_name = f'{registry}/{image_name}'
    tags = get_image_tags(event, full_image_name)

    info(f'Will create {len(tags)} tags')

    # Build arguments
    build_args = {
        'BUILD_DATE': event.sha,
        'VCS_REF': event.sha[:8],
    }

    image_id = None
    scan_results = {}

    try:
        # Build image
        with group('Building Image'):
            image_id = docker_build(dockerfile, context, tags[0], build_args)

        # Tag with all tags
        with group('Tagging Image'):
            for tag in tags[1:]:
                subprocess.run(['docker', 'tag', tags[0], tag], check=True)
                info(f'✓ Tagged as {tag}')

        # Security scan
        if scan_enabled:
            with group('Security Scan'):
                scan_results = scan_image(tags[0])

        # Push to registry
        if push_enabled:
            if not username or not password:
                warning(
                    'Username/password not provided, skipping push',
                    title='Push Skipped',
                )
            else:
                with group('Pushing to Registry'):
                    docker_login(registry, username, password)
                    for tag in tags:
                        docker_push(tag)
        else:
            info('Push disabled, skipping')

        # Create summary
        with group('Creating Summary'):
            create_summary(full_image_name, tags, image_id or '', scan_results)

        # Set outputs
        set_output('image', full_image_name)
        set_output('tags', ','.join(tags))
        if image_id:
            set_output('image-id', image_id)

        info('✓ Docker build and push complete')
        return 0

    except Exception as e:
        error(f'Action failed: {e}', title='Build Failed')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
```

## Contributing Examples

Have a great example? Contribute it!

1. Fork the repository
2. Add your example documentation to this page
3. Document it clearly with comments
4. Submit a pull request

See {doc}`/CONTRIBUTING` for guidelines.
