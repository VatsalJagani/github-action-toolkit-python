# Job Summary Templates

Pre-built templates for common job summary use cases.

## Overview

This page provides template patterns for creating job summaries for common scenarios like test reports, coverage reports, deployment summaries, and benchmark results.

## Examples

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
