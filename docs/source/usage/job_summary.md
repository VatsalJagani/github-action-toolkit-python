# Job Summary

Create rich, formatted summaries for GitHub Actions workflows using a fluent builder API. Job summaries appear on the workflow run summary page and support tables, code blocks, images, collapsible sections, and more.

## Table of Contents

- [Fluent Builder API](#fluent-builder-api)
- [Basic Elements](#basic-elements)
- [Tables](#tables)
- [Code Blocks](#code-blocks)
- [Images](#images)
- [Collapsible Sections](#collapsible-sections)
- [Template API](#template-api)
- [Legacy Functions](#legacy-functions)
- [Size Limits and Security](#size-limits-and-security)

## Fluent Builder API

The `JobSummary` class provides a fluent API for building rich summaries. All methods return `self` for easy chaining.

### Basic Usage

```python
from github_action_toolkit import JobSummary

summary = JobSummary()
summary.add_heading("Test Results", 1)
summary.add_separator()
summary.add_list(["Test 1: ✓ Passed", "Test 2: ✓ Passed", "Test 3: ✗ Failed"])
summary.write()
```

### Fluent Chaining

Chain multiple methods for concise code:

```python
summary = JobSummary()
(summary
    .add_heading("CI Pipeline Report", 1)
    .add_separator()
    .add_quote("All tests passed!")
    .add_break()
    .add_link("View Dashboard", "https://example.com")
    .write()
)
```

## Basic Elements

### Headings

Add headings at levels 1-6:

```python
summary.add_heading("Main Title", 1)
summary.add_heading("Subtitle", 2)
summary.add_heading("Section", 3)
```

### Text and Line Breaks

Add raw text, line breaks, and separators:

```python
summary.add_raw("Plain text content")
summary.add_eol()  # Add newline
summary.add_break()  # Add <br>
summary.add_separator()  # Add <hr>
```

### Quotes

Add blockquotes with optional citations:

```python
summary.add_quote("This is a quote")
summary.add_quote("Quote with citation", cite="Author Name")
```

### Links

Add hyperlinks:

```python
summary.add_link("GitHub", "https://github.com")
```

### Lists

Create ordered or unordered lists:

```python
# Unordered list
summary.add_list(["Item 1", "Item 2", "Item 3"])

# Ordered list
summary.add_list(["First", "Second", "Third"], ordered=True)
```

## Tables

Create tables with headers and rows. The first row is automatically treated as headers.

### Simple Tables

```python
rows = [
    ["Name", "Status", "Duration"],
    ["test_auth", "✓ Pass", "0.5s"],
    ["test_db", "✓ Pass", "1.2s"],
    ["test_api", "✗ Fail", "0.8s"],
]
summary.add_table(rows)
```

### Advanced Tables with Cell Options

Use dictionaries for cells that need special attributes:

```python
rows = [
    [{"data": "Header 1", "header": True}, {"data": "Header 2", "header": True}],
    [{"data": "Spanning Cell", "colspan": "2"}],
    ["Regular", "Cells"],
]
summary.add_table(rows)
```

Cell dictionary keys:
- `data`: Cell content (required)
- `header`: True to render as `<th>` instead of `<td>`
- `colspan`: Number of columns to span
- `rowspan`: Number of rows to span

## Code Blocks

Add code blocks with optional syntax highlighting:

```python
# Without language
summary.add_code_block("print('hello world')")

# With language
summary.add_code_block("""
def greet(name):
    return f"Hello, {name}!"
""", "python")
```

## Images

Add images with alt text and optional dimensions:

```python
# Basic image
summary.add_image("https://example.com/image.png", "Alt text")

# With dimensions
summary.add_image(
    "https://example.com/chart.png",
    "Performance Chart",
    width="400",
    height="300"
)
```

## Collapsible Sections

Create collapsible details sections:

```python
summary.add_details(
    "Click to expand",
    "Hidden content that appears when expanded"
)
```

## Template API

The `JobSummaryTemplate` class provides pre-built templates for common use cases.

### Test Report

```python
from github_action_toolkit import JobSummaryTemplate

summary = JobSummaryTemplate.test_report(
    title="Unit Test Results",
    passed=45,
    failed=3,
    skipped=2,
    duration="12.5s"
)
summary.write()
```

### Coverage Report

```python
coverage_data = {
    "core/auth.py": 98.5,
    "core/database.py": 92.3,
    "api/handlers.py": 87.6,
}

summary = JobSummaryTemplate.coverage_report(
    "Code Coverage",
    coverage_data
)
summary.write()
```

### Deployment Report

```python
summary = JobSummaryTemplate.deployment_report(
    title="Production Deployment",
    environment="production",
    status="success",
    version="v2.5.0",
    url="https://app.example.com"
)
summary.write()
```

### Benchmark Report

```python
benchmarks = {
    "API Response Time": {
        "Average": "125ms",
        "P95": "250ms",
        "P99": "500ms",
    },
    "Database Query": {
        "Average": "45ms",
        "P95": "80ms",
    },
}

summary = JobSummaryTemplate.benchmark_report(
    "Performance Benchmarks",
    benchmarks
)
summary.write()
```

### Combining Templates

Templates return `JobSummary` objects, so you can add custom content:

```python
summary = JobSummaryTemplate.test_report(
    title="CI Results",
    passed=50,
    failed=0,
    duration="15.2s"
)

# Add custom content
summary.add_separator()
summary.add_heading("Additional Notes", 2)
summary.add_quote("All quality gates passed!")
summary.write()
```

## Legacy Functions

These functions provide backward compatibility with earlier versions.

### `append_job_summary(markdown_text)`

Append markdown text to the job summary:

```python
from github_action_toolkit import append_job_summary

append_job_summary("# Test Summary")
append_job_summary("- Point 1")
```

### `overwrite_job_summary(markdown_text)`

Replace the entire job summary:

```python
from github_action_toolkit import overwrite_job_summary

overwrite_job_summary("# New Summary")
```

### `remove_job_summary()`

Remove the job summary file:

```python
from github_action_toolkit import remove_job_summary

remove_job_summary()
```

## Size Limits and Security

### Size Limits

Job summaries are limited to 1 MiB (1,048,576 bytes). The API automatically enforces this limit:

```python
summary = JobSummary()
summary.add_raw("..." * 1000000)  # Large content
summary.write()  # Raises ValueError if too large
```

### Content Sanitization

All content is automatically sanitized to prevent XSS attacks. HTML special characters are escaped:

```python
summary = JobSummary()
summary.add_heading("<script>alert('xss')</script>")
# Rendered as: &lt;script&gt;alert('xss')&lt;/script&gt;
```

### Buffer Management

Control when content is written:

```python
summary = JobSummary()
summary.add_heading("Title", 1)
summary.add_raw("Content")

# Check if empty
if not summary.is_empty():
    # Get as string without writing
    content = summary.stringify()
    
    # Clear buffer
    summary.clear()
    
    # Write to file (buffer is cleared after write)
    summary.write()
    
    # Overwrite file
    summary.write(overwrite=True)
```

## Complete Example

Here's a complete example combining multiple features:

```python
from github_action_toolkit import JobSummary, JobSummaryTemplate

# Use template for test results
summary = JobSummaryTemplate.test_report(
    title="CI Pipeline Results",
    passed=42,
    failed=0,
    duration="8.5s"
)

# Add coverage information
summary.add_separator()
summary.add_heading("Code Coverage", 2)
summary.add_table([
    ["Module", "Coverage"],
    ["Core", "95%"],
    ["API", "92%"],
    ["Utils", "87%"],
])

# Add deployment info
summary.add_separator()
summary.add_heading("Deployment", 2)
summary.add_quote("✓ Successfully deployed to staging")
summary.add_link("View Application", "https://staging.example.com")

# Add collapsible logs
summary.add_break()
summary.add_details("View Build Logs", """
Building...
Running tests...
All tests passed!
Deploying...
Deployment successful!
""")

# Write the summary
summary.write()
```

## Reference

For more information, see the [GitHub Actions documentation on job summaries](https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#adding-a-job-summary).
