# pyright: reportPrivateUsage=false
# pyright: reportUnusedVariable=false
# pyright: reportUnknownMemberType=false

"""
Snapshot tests for job summaries and message formatting.
These tests capture the expected output format and detect unintended changes.
"""

import os
from typing import Any
from unittest import mock

import github_action_toolkit as gat


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


def test_job_summary_overwrite(snapshot: Any, tmpdir: Any) -> None:
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
