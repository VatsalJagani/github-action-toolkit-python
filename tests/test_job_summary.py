# pyright: reportPrivateUsage=false
# pyright: reportUnusedVariable=false
# pyright: reportUnusedParameter=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUnknownMemberType=false

import os
from typing import Any
from unittest import mock

import pytest

import github_action_toolkit as gat
import github_action_toolkit.job_summary as gat_job_summary


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("# test", "# test"),
        ("# test%0A", "# test\n"),
        ("- %25test", "- %test"),
        ("**%0Dtest**", "**\rtest**"),
    ],
)
def test__clean_markdown_string(test_input: str, expected: str) -> None:
    assert gat_job_summary._clean_markdown_string(test_input) == expected


def test_append_job_summary(tmpdir: Any) -> None:
    file = tmpdir.join("summary")

    with mock.patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": file.strpath}):
        gat.append_job_summary("# TEST")
        gat.append_job_summary("- point 1")

    assert file.read() == "# TEST\n- point 1\n"


def test_overwrite_job_summary(tmpdir: Any) -> None:
    file = tmpdir.join("summary")

    with mock.patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": file.strpath}):
        gat.append_job_summary("# TEST")
        gat.overwrite_job_summary("- point 1")

    assert file.read() == "- point 1\n"


def test_remove_job_summary(tmpdir: Any) -> None:
    file = tmpdir.join("summary")

    with mock.patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": file.strpath}):
        gat.remove_job_summary()

    assert os.path.isfile(file.strpath) is False


# JobSummary builder tests


def test_job_summary_basic_usage() -> None:
    summary = gat.JobSummary()
    assert summary.is_empty()

    summary.add_raw("Hello World")
    assert not summary.is_empty()
    assert summary.stringify() == "Hello World"

    summary.clear()
    assert summary.is_empty()


def test_job_summary_add_heading() -> None:
    summary = gat.JobSummary()
    summary.add_heading("Test Heading", 1)
    assert "<h1>Test Heading</h1>" in summary.stringify()

    summary.clear()
    summary.add_heading("Subheading", 2)
    assert "<h2>Subheading</h2>" in summary.stringify()

    summary.clear()
    summary.add_heading("Test", 10)  # Invalid level, should default to 1
    assert "<h1>Test</h1>" in summary.stringify()


def test_job_summary_add_separator() -> None:
    summary = gat.JobSummary()
    summary.add_separator()
    assert "<hr>" in summary.stringify()


def test_job_summary_add_break() -> None:
    summary = gat.JobSummary()
    summary.add_break()
    assert "<br>" in summary.stringify()


def test_job_summary_add_quote() -> None:
    summary = gat.JobSummary()
    summary.add_quote("This is a quote")
    assert "<blockquote>This is a quote</blockquote>" in summary.stringify()

    summary.clear()
    summary.add_quote("Quote with citation", "Author")
    result = summary.stringify()
    assert "<blockquote" in result
    assert 'cite="Author"' in result
    assert "Quote with citation" in result


def test_job_summary_add_link() -> None:
    summary = gat.JobSummary()
    summary.add_link("GitHub", "https://github.com")
    result = summary.stringify()
    assert '<a href="https://github.com">GitHub</a>' in result


def test_job_summary_add_code_block() -> None:
    summary = gat.JobSummary()
    summary.add_code_block("print('hello')")
    assert "<pre><code>print('hello')</code></pre>" in summary.stringify()

    summary.clear()
    summary.add_code_block("def test(): pass", "python")
    result = summary.stringify()
    assert '<pre lang="python">' in result
    assert "def test(): pass" in result


def test_job_summary_add_list() -> None:
    summary = gat.JobSummary()
    summary.add_list(["Item 1", "Item 2", "Item 3"])
    result = summary.stringify()
    assert "<ul>" in result
    assert "<li>Item 1</li>" in result
    assert "<li>Item 2</li>" in result
    assert "<li>Item 3</li>" in result
    assert "</ul>" in result

    summary.clear()
    summary.add_list(["First", "Second"], ordered=True)
    result = summary.stringify()
    assert "<ol>" in result
    assert "<li>First</li>" in result
    assert "</ol>" in result


def test_job_summary_add_table_simple() -> None:
    summary = gat.JobSummary()
    rows = [
        ["Header 1", "Header 2"],
        ["Row 1 Col 1", "Row 1 Col 2"],
        ["Row 2 Col 1", "Row 2 Col 2"],
    ]
    summary.add_table(rows)
    result = summary.stringify()
    assert "<table>" in result
    assert "<th>Header 1</th>" in result
    assert "<th>Header 2</th>" in result
    assert "<td>Row 1 Col 1</td>" in result
    assert "</table>" in result


def test_job_summary_add_table_with_dict_cells() -> None:
    summary = gat.JobSummary()
    rows: list[list[str | dict[str, str | bool | int]]] = [
        [{"data": "Header 1", "header": True}, {"data": "Header 2", "header": True}],
        [{"data": "Spanning", "colspan": "2"}],
        ["Regular", "Cell"],
    ]
    summary.add_table(rows)
    result = summary.stringify()
    assert "<th>Header 1</th>" in result
    assert "<th>Header 2</th>" in result
    assert 'colspan="2"' in result
    assert "<td>Regular</td>" in result


def test_job_summary_add_details() -> None:
    summary = gat.JobSummary()
    summary.add_details("Click to expand", "Hidden content here")
    result = summary.stringify()
    assert "<details>" in result
    assert "<summary>Click to expand</summary>" in result
    assert "Hidden content here" in result
    assert "</details>" in result


def test_job_summary_add_image() -> None:
    summary = gat.JobSummary()
    summary.add_image("https://example.com/image.png", "Test Image")
    result = summary.stringify()
    assert '<img src="https://example.com/image.png" alt="Test Image">' in result

    summary.clear()
    summary.add_image("image.png", "Alt text", width="100", height="50")
    result = summary.stringify()
    assert 'width="100"' in result
    assert 'height="50"' in result


def test_job_summary_sanitization() -> None:
    summary = gat.JobSummary()
    summary.add_heading("<script>alert('xss')</script>")
    result = summary.stringify()
    assert "&lt;script&gt;" in result
    assert "<script>" not in result


def test_job_summary_fluent_chaining() -> None:
    summary = gat.JobSummary()
    result = (
        summary.add_heading("Test Report", 1)
        .add_separator()
        .add_list(["Test 1: Pass", "Test 2: Pass"])
        .add_break()
        .add_quote("All tests passed!")
        .stringify()
    )
    assert "<h1>Test Report</h1>" in result
    assert "<hr>" in result
    assert "<ul>" in result
    assert "<blockquote>" in result


def test_job_summary_write(tmpdir: Any) -> None:
    file = tmpdir.join("summary")

    with mock.patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": file.strpath}):
        summary = gat.JobSummary()
        summary.add_heading("Test Summary", 1).add_raw("Some content").write()

        assert "<h1>Test Summary</h1>" in file.read()
        assert summary.is_empty()  # Buffer should be cleared after write


def test_job_summary_write_overwrite(tmpdir: Any) -> None:
    file = tmpdir.join("summary")
    file.write("Old content")

    with mock.patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": file.strpath}):
        summary = gat.JobSummary()
        summary.add_heading("New Summary", 1).write(overwrite=True)

        content = file.read()
        assert "<h1>New Summary</h1>" in content
        assert "Old content" not in content


def test_job_summary_write_append(tmpdir: Any) -> None:
    file = tmpdir.join("summary")
    file.write("Existing content\n")

    with mock.patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": file.strpath}):
        summary = gat.JobSummary()
        summary.add_heading("Appended Summary", 1).write(overwrite=False)

        content = file.read()
        assert "Existing content" in content
        assert "<h1>Appended Summary</h1>" in content


def test_job_summary_write_no_env_var() -> None:
    with mock.patch.dict(os.environ, {}, clear=True):
        summary = gat.JobSummary()
        summary.add_heading("Test", 1)

        with pytest.raises(ValueError, match="GITHUB_STEP_SUMMARY"):
            summary.write()


def test_job_summary_size_limit(tmpdir: Any) -> None:
    file = tmpdir.join("summary")

    with mock.patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": file.strpath}):
        summary = gat.JobSummary()
        large_content = "x" * (gat_job_summary.MAX_SUMMARY_SIZE + 1)
        summary.add_raw(large_content)

        with pytest.raises(ValueError, match="Summary exceeds maximum size"):
            summary.write()


# JobSummaryTemplate tests


def test_template_test_report() -> None:
    summary = gat.JobSummaryTemplate.test_report(
        title="Unit Tests", passed=10, failed=2, skipped=1, duration="5.2s"
    )
    result = summary.stringify()
    assert "<h1>Unit Tests</h1>" in result
    assert "2 test(s) failed" in result
    assert "<td>Total Tests</td>" in result
    assert "<td>13</td>" in result
    assert "<td>10</td>" in result
    assert "<td>2</td>" in result
    assert "<td>1</td>" in result
    assert "5.2s" in result


def test_template_test_report_all_passed() -> None:
    summary = gat.JobSummaryTemplate.test_report(title="Unit Tests", passed=10, failed=0)
    result = summary.stringify()
    assert "All tests passed" in result
    assert "<td>10</td>" in result


def test_template_coverage_report() -> None:
    modules = {"core": 95.5, "utils": 87.2, "api": 92.0}
    summary = gat.JobSummaryTemplate.coverage_report("Code Coverage", modules)
    result = summary.stringify()
    assert "<h1>Code Coverage</h1>" in result
    assert "Good coverage" in result
    assert "91.6%" in result  # Average
    assert "core" in result
    assert "95.5%" in result


def test_template_coverage_report_empty() -> None:
    summary = gat.JobSummaryTemplate.coverage_report("Code Coverage", {})
    result = summary.stringify()
    assert "No coverage data available" in result


def test_template_deployment_report() -> None:
    summary = gat.JobSummaryTemplate.deployment_report(
        title="Deployment",
        environment="production",
        status="success",
        version="1.2.3",
        url="https://example.com",
    )
    result = summary.stringify()
    assert "<h1>Deployment</h1>" in result
    assert "production" in result
    assert "success" in result
    assert "1.2.3" in result
    assert "https://example.com" in result


def test_template_benchmark_report() -> None:
    benchmarks = {
        "API Response Time": {"Average": "120ms", "P95": "250ms", "P99": "500ms"},
        "Database Query": {"Average": "45ms", "P95": "80ms"},
    }
    summary = gat.JobSummaryTemplate.benchmark_report("Performance Benchmarks", benchmarks)
    result = summary.stringify()
    assert "<h1>Performance Benchmarks</h1>" in result
    assert "API Response Time" in result
    assert "120ms" in result
    assert "Database Query" in result
    assert "45ms" in result


def test_template_benchmark_report_empty() -> None:
    summary = gat.JobSummaryTemplate.benchmark_report("Performance Benchmarks", {})
    result = summary.stringify()
    assert "No benchmark data available" in result


# Snapshot tests for job summary formatting


def test_job_summary_formatting(snapshot: Any, tmpdir: Any) -> None:
    """Snapshot test for job summary formatting."""
    file = tmpdir.join("summary")

    with mock.patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": file.strpath}):
        gat.append_job_summary("# Test Summary")
        gat.append_job_summary("## Section 1")
        gat.append_job_summary("- Item 1")
        gat.append_job_summary("- Item 2")
        gat.append_job_summary("")
        gat.append_job_summary("## Section 2")
        gat.append_job_summary("Some **bold** text and *italic* text.")

    result = file.read()
    assert result == snapshot


def test_job_summary_with_special_chars(snapshot: Any, tmpdir: Any) -> None:
    """Snapshot test for job summary with special characters."""
    file = tmpdir.join("summary")

    with mock.patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": file.strpath}):
        gat.append_job_summary("# Test with %25 percent")
        gat.append_job_summary("Line with %0A newline")
        gat.append_job_summary("Line with %0D carriage return")

    result = file.read()
    assert result == snapshot


def test_job_summary_overwrite_snapshot(snapshot: Any, tmpdir: Any) -> None:
    """Snapshot test for job summary overwrite."""
    file = tmpdir.join("summary")

    with mock.patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": file.strpath}):
        gat.append_job_summary("# Initial content")
        gat.append_job_summary("- Point 1")
        gat.overwrite_job_summary("# New content")
        gat.append_job_summary("- New point")

    result = file.read()
    assert result == snapshot


def test_job_summary_complex_markdown(snapshot: Any, tmpdir: Any) -> None:
    """Snapshot test for complex markdown formatting."""
    file = tmpdir.join("summary")

    complex_markdown = """
# GitHub Action Summary

## Build Results
- ✅ Build passed
- ✅ Tests passed
- ⚠️  Coverage at 85%

## Details
| Metric | Value |
|--------|-------|
| Tests  | 104   |
| Lines  | 397   |

### Code Quality
All checks passed successfully!
"""

    with mock.patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": file.strpath}):
        gat.append_job_summary(complex_markdown)

    result = file.read()
    assert result == snapshot


# Additional snapshot tests for JobSummary builder


def test_job_summary_builder_table_snapshot(snapshot: Any) -> None:
    """Snapshot test for JobSummary table building."""
    summary = gat.JobSummary()
    rows = [
        ["Name", "Status", "Duration"],
        ["Build", "✅ Success", "2m 15s"],
        ["Test", "✅ Success", "5m 42s"],
        ["Deploy", "⚠️  Warning", "1m 30s"],
    ]
    summary.add_heading("CI/CD Pipeline", 2).add_table(rows)
    result = summary.stringify()
    assert result == snapshot


def test_job_summary_builder_code_blocks_snapshot(snapshot: Any) -> None:
    """Snapshot test for JobSummary code blocks."""
    summary = gat.JobSummary()
    summary.add_heading("Code Examples", 2).add_code_block(
        'def hello():\n    print("Hello, World!")', "python"
    ).add_break().add_code_block("npm install github-action-toolkit", "bash")
    result = summary.stringify()
    assert result == snapshot


def test_job_summary_builder_mixed_content_snapshot(snapshot: Any) -> None:
    """Snapshot test for JobSummary with mixed content types."""
    summary = gat.JobSummary()
    (
        summary.add_heading("Test Report", 1)
        .add_separator()
        .add_quote("Testing is an integral part of software development.", "Anonymous")
        .add_break()
        .add_list(
            ["Unit tests: 150 passed", "Integration tests: 45 passed", "E2E tests: 20 passed"]
        )
        .add_separator()
        .add_link("View detailed report", "https://example.com/report")
        .add_details("Click to expand logs", "Log content here\nLine 2\nLine 3")
    )
    result = summary.stringify()
    assert result == snapshot


def test_job_summary_template_test_report_snapshot(snapshot: Any) -> None:
    """Snapshot test for test report template."""
    summary = gat.JobSummaryTemplate.test_report(
        title="Integration Test Results",
        passed=85,
        failed=3,
        skipped=2,
        duration="12m 34s",
    )
    result = summary.stringify()
    assert result == snapshot


def test_job_summary_template_coverage_report_snapshot(snapshot: Any) -> None:
    """Snapshot test for coverage report template."""
    modules = {
        "authentication": 92.5,
        "database": 88.3,
        "api": 95.1,
        "utils": 78.9,
        "models": 91.0,
    }
    summary = gat.JobSummaryTemplate.coverage_report("Test Coverage Report", modules)
    result = summary.stringify()
    assert result == snapshot


def test_job_summary_sanitization_snapshot(snapshot: Any) -> None:
    """Snapshot test for HTML sanitization in job summary."""
    summary = gat.JobSummary()
    summary.add_heading("<script>alert('xss')</script> Malicious Title").add_raw(
        "<img src=x onerror=alert('xss')>"
    ).add_quote("<b>Bold</b> and <i>italic</i> tags")
    result = summary.stringify()
    assert result == snapshot
