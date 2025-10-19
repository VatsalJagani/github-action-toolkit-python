# Job Summary Templates

Pre-built templates for common job summary use cases using the `JobSummaryTemplate` class.

## Overview

The `JobSummaryTemplate` class provides static methods that generate pre-configured job summaries for common scenarios like test reports, coverage reports, deployment summaries, and benchmark results. These templates save you from having to manually build these common patterns.

## Available Templates

### Test Report

Create a formatted test report summary.

```python
from github_action_toolkit import JobSummaryTemplate

# Create test report
summary = JobSummaryTemplate.test_report(
    title="Unit Test Results",
    passed=145,
    failed=3,
    skipped=2,
    duration="2m 34s"
)

# Write to job summary
summary.write()
```

**Parameters:**
- `title`: Report title
- `passed`: Number of passed tests
- `failed`: Number of failed tests
- `skipped`: Number of skipped tests (optional)
- `duration`: Test duration string (optional)

**Output includes:**
- Status quote (✓ All tests passed or ✗ X test(s) failed)
- Table with test metrics
- Automatic total calculation

### Coverage Report

Create a coverage report with visual indicators.

```python
from github_action_toolkit import JobSummaryTemplate

# Create coverage report
coverage_data = {
    "src/core.py": 92.5,
    "src/utils.py": 78.3,
    "src/helpers.py": 65.0,
}

summary = JobSummaryTemplate.coverage_report(
    title="Code Coverage Report",
    modules=coverage_data
)

summary.write()
```

**Parameters:**
- `title`: Report title
- `modules`: Dict mapping module names to coverage percentages

**Output includes:**
- Average coverage with status (✓ Good coverage for ≥80% or ⚠ Low coverage)
- Table with per-module coverage
- Visual indicators (✓ for ≥80%, ⚠ for ≥60%, ✗ for <60%)

### Deployment Report

Create a deployment summary with environment details.

```python
from github_action_toolkit import JobSummaryTemplate

# Create deployment report
summary = JobSummaryTemplate.deployment_report(
    title="Production Deployment",
    environment="production",
    status="success",
    version="v2.1.4",
    url="https://myapp.example.com"
)

summary.write()
```

**Parameters:**
- `title`: Report title
- `environment`: Deployment environment (e.g., 'production', 'staging')
- `status`: Deployment status (e.g., 'success', 'failed')
- `version`: Version string (optional)
- `url`: Deployment URL (optional)

**Output includes:**
- Status quote with emoji (✓ for success, ✗ for failure)
- Table with deployment details
- Clickable link to deployment (if URL provided)

### Benchmark Report

Create a benchmark results summary.

```python
from github_action_toolkit import JobSummaryTemplate

# Create benchmark report
benchmarks = {
    "Query Performance": {
        "Avg Response Time": "42ms",
        "P95 Response Time": "89ms",
        "Requests/sec": "2,341",
    },
    "Memory Usage": {
        "Peak Memory": "512MB",
        "Avg Memory": "256MB",
    },
}

summary = JobSummaryTemplate.benchmark_report(
    title="Performance Benchmarks",
    benchmarks=benchmarks
)

summary.write()
```

**Parameters:**
- `title`: Report title
- `benchmarks`: Dict mapping benchmark names to metric dicts (metric name → value)

**Output includes:**
- Heading for each benchmark category
- Table of metrics for each benchmark
- Clean formatting with breaks between sections

## Customizing Templates

Templates return a `JobSummary` object, so you can further customize before writing:

```python
from github_action_toolkit import JobSummaryTemplate

# Start with template
summary = JobSummaryTemplate.test_report(
    title="Test Results",
    passed=100,
    failed=0
)

# Add custom content
summary.add_separator()
summary.add_heading("Additional Notes", 2)
summary.add_raw("All tests passed on first attempt!")

# Write complete summary
summary.write()
```
