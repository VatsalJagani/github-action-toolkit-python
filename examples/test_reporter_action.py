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
