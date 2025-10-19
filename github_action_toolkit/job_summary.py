from __future__ import annotations

import html
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Self

# Maximum size for a job summary in bytes (1 MiB)
MAX_SUMMARY_SIZE = 1024 * 1024


def _clean_markdown_string(markdown_string: str) -> str:
    """
    Removes `%25, %0D, %0A` characters from a string.

    :param markdown_string: string with markdown content
    :returns: string after escaping
    """
    return str(markdown_string).replace("%25", "%").replace("%0D", "\r").replace("%0A", "\n")


def _sanitize_content(content: str | int | bool) -> str:
    """
    Sanitize content by escaping HTML to prevent XSS attacks.

    :param content: raw content to sanitize
    :returns: sanitized content
    """
    return html.escape(str(content), quote=False)


def append_job_summary(markdown_text: str) -> None:
    """
    appends summery of the job to the GitHub Action Summary page.

    :param markdown_text: string with Markdown text
    :returns: None
    """
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
        f.write(f"{_clean_markdown_string(markdown_text)}\n")


def overwrite_job_summary(markdown_text: str) -> None:
    """
    overwrites summary of the job for the GitHub Action Summary page.

    :param markdown_text: string with Markdown text
    :returns: None
    """
    with open(os.environ["GITHUB_STEP_SUMMARY"], "w") as f:
        f.write(f"{_clean_markdown_string(markdown_text)}\n")


def remove_job_summary() -> None:
    """
    removes summary file for the job.

    :returns: None
    """
    try:
        os.remove(os.environ["GITHUB_STEP_SUMMARY"])
    except (KeyError, FileNotFoundError):
        pass


class JobSummary:
    """
    Fluent builder API for constructing GitHub Actions job summaries with Markdown.

    Provides methods to build rich summaries with tables, code blocks, images,
    collapsible sections, and more. Enforces size limits and sanitizes content.
    """

    def __init__(self) -> None:
        self._buffer: list[str] = []

    def add_raw(self, text: str, add_eol: bool = False) -> Self:
        """
        Add raw markdown text to the summary.

        :param text: markdown text to add
        :param add_eol: whether to add a newline after the text
        :returns: self for chaining
        """
        self._buffer.append(text)
        if add_eol:
            self._buffer.append("\n")
        return self

    def add_eol(self) -> Self:
        """
        Add a newline to the summary.

        :returns: self for chaining
        """
        return self.add_raw("\n")

    def add_heading(self, text: str, level: int = 1) -> Self:
        """
        Add a heading to the summary.

        :param text: heading text
        :param level: heading level (1-6)
        :returns: self for chaining
        """
        if level < 1 or level > 6:
            level = 1
        tag = f"h{level}"
        self._buffer.append(f"<{tag}>{_sanitize_content(text)}</{tag}>\n")
        return self

    def add_separator(self) -> Self:
        """
        Add a horizontal rule to the summary.

        :returns: self for chaining
        """
        self._buffer.append("<hr>\n")
        return self

    def add_break(self) -> Self:
        """
        Add a line break to the summary.

        :returns: self for chaining
        """
        self._buffer.append("<br>\n")
        return self

    def add_quote(self, text: str, cite: str | None = None) -> Self:
        """
        Add a blockquote to the summary.

        :param text: quote text
        :param cite: optional citation
        :returns: self for chaining
        """
        cite_attr = f' cite="{_sanitize_content(cite)}"' if cite else ""
        self._buffer.append(f"<blockquote{cite_attr}>{_sanitize_content(text)}</blockquote>\n")
        return self

    def add_link(self, text: str, href: str) -> Self:
        """
        Add a link to the summary.

        :param text: link text
        :param href: link URL
        :returns: self for chaining
        """
        self._buffer.append(f'<a href="{_sanitize_content(href)}">{_sanitize_content(text)}</a>')
        return self

    def add_code_block(self, code: str, lang: str | None = None) -> Self:
        """
        Add a code block to the summary.

        :param code: code content
        :param lang: optional language for syntax highlighting
        :returns: self for chaining
        """
        lang_attr = f' lang="{_sanitize_content(lang)}"' if lang else ""
        self._buffer.append(f"<pre{lang_attr}><code>{_sanitize_content(code)}</code></pre>\n")
        return self

    def add_list(self, items: Sequence[str], ordered: bool = False) -> Self:
        """
        Add a list to the summary.

        :param items: list items
        :param ordered: whether the list should be ordered (numbered)
        :returns: self for chaining
        """
        tag = "ol" if ordered else "ul"
        self._buffer.append(f"<{tag}>\n")
        for item in items:
            self._buffer.append(f"<li>{_sanitize_content(item)}</li>\n")
        self._buffer.append(f"</{tag}>\n")
        return self

    def add_table(self, rows: Sequence[Sequence[str | dict[str, str | bool | int]]]) -> Self:
        """
        Add a table to the summary.

        The first row is treated as the header. Each cell can be a string or a dict
        with keys: 'data' (required), 'header' (bool), 'colspan', 'rowspan'.

        :param rows: table rows, where each row is a sequence of cells
        :returns: self for chaining
        """
        if not rows:
            return self

        self._buffer.append("<table>\n")

        for idx, row in enumerate(rows):
            self._buffer.append("<tr>\n")
            for cell in row:
                if isinstance(cell, dict):
                    data = cell.get("data", "")
                    is_header = cell.get("header", idx == 0)
                    colspan = cell.get("colspan")
                    rowspan = cell.get("rowspan")

                    tag = "th" if is_header else "td"
                    attrs = ""
                    if colspan:
                        attrs += f' colspan="{colspan}"'
                    if rowspan:
                        attrs += f' rowspan="{rowspan}"'

                    self._buffer.append(f"<{tag}{attrs}>{_sanitize_content(data)}</{tag}>\n")
                else:
                    tag = "th" if idx == 0 else "td"
                    self._buffer.append(f"<{tag}>{_sanitize_content(cell)}</{tag}>\n")
            self._buffer.append("</tr>\n")

        self._buffer.append("</table>\n")
        return self

    def add_details(self, label: str, content: str) -> Self:
        """
        Add a collapsible details section to the summary.

        :param label: summary label (visible when collapsed)
        :param content: content to show when expanded
        :returns: self for chaining
        """
        self._buffer.append("<details>\n")
        self._buffer.append(f"<summary>{_sanitize_content(label)}</summary>\n")
        self._buffer.append(f"{_sanitize_content(content)}\n")
        self._buffer.append("</details>\n")
        return self

    def add_image(
        self, src: str, alt: str, width: str | None = None, height: str | None = None
    ) -> Self:
        """
        Add an image to the summary.

        :param src: image URL or path
        :param alt: alt text for the image
        :param width: optional width
        :param height: optional height
        :returns: self for chaining
        """
        attrs = f'src="{_sanitize_content(src)}" alt="{_sanitize_content(alt)}"'
        if width:
            attrs += f' width="{_sanitize_content(width)}"'
        if height:
            attrs += f' height="{_sanitize_content(height)}"'
        self._buffer.append(f"<img {attrs}>\n")
        return self

    def clear(self) -> Self:
        """
        Clear the buffer without writing.

        :returns: self for chaining
        """
        self._buffer.clear()
        return self

    def stringify(self) -> str:
        """
        Get the current buffer content as a string.

        :returns: the buffer content
        """
        return "".join(self._buffer)

    def is_empty(self) -> bool:
        """
        Check if the buffer is empty.

        :returns: True if empty, False otherwise
        """
        return len(self._buffer) == 0

    def write(self, overwrite: bool = False) -> Self:
        """
        Write the buffer to the job summary file.

        :param overwrite: whether to overwrite the file or append
        :raises ValueError: if the summary exceeds the maximum size
        :returns: self for chaining
        """
        content = self.stringify()

        if len(content.encode("utf-8")) > MAX_SUMMARY_SIZE:
            raise ValueError(
                f"Summary exceeds maximum size of {MAX_SUMMARY_SIZE} bytes "
                f"({MAX_SUMMARY_SIZE // 1024} KiB)"
            )

        summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
        if not summary_file:
            raise ValueError("GITHUB_STEP_SUMMARY environment variable not set")

        mode = "w" if overwrite else "a"
        Path(summary_file).write_text(content, encoding="utf-8") if overwrite else Path(
            summary_file
        ).open(mode, encoding="utf-8").write(content)

        self._buffer.clear()
        return self


class JobSummaryTemplate:
    """
    Reusable templates for common job summary patterns.

    Templates provide pre-built patterns for common use cases like test reports,
    coverage reports, and deployment summaries.
    """

    @staticmethod
    def test_report(
        title: str,
        passed: int,
        failed: int,
        skipped: int = 0,
        duration: str | None = None,
    ) -> JobSummary:
        """
        Create a test report summary.

        :param title: report title
        :param passed: number of passed tests
        :param failed: number of failed tests
        :param skipped: number of skipped tests
        :param duration: optional test duration
        :returns: JobSummary with test report
        """
        summary = JobSummary()
        summary.add_heading(title, 1)
        summary.add_separator()

        total = passed + failed + skipped
        status = "✓ All tests passed" if failed == 0 else f"✗ {failed} test(s) failed"

        summary.add_quote(status)

        rows = [
            ["Metric", "Count"],
            ["Total Tests", str(total)],
            ["✓ Passed", str(passed)],
        ]
        if failed > 0:
            rows.append(["✗ Failed", str(failed)])
        if skipped > 0:
            rows.append(["⊘ Skipped", str(skipped)])
        if duration:
            rows.append(["Duration", duration])

        summary.add_table(rows)
        return summary

    @staticmethod
    def coverage_report(title: str, modules: dict[str, float]) -> JobSummary:
        """
        Create a coverage report summary.

        :param title: report title
        :param modules: dict mapping module names to coverage percentages
        :returns: JobSummary with coverage report
        """
        summary = JobSummary()
        summary.add_heading(title, 1)
        summary.add_separator()

        if not modules:
            summary.add_raw("No coverage data available")
            return summary

        avg_coverage = sum(modules.values()) / len(modules)
        status = "✓ Good coverage" if avg_coverage >= 80 else "⚠ Low coverage"
        summary.add_quote(f"{status}: {avg_coverage:.1f}% average")

        rows = [["Module", "Coverage"]]
        for module, coverage in sorted(modules.items()):
            emoji = "✓" if coverage >= 80 else "⚠" if coverage >= 60 else "✗"
            rows.append([module, f"{emoji} {coverage:.1f}%"])

        summary.add_table(rows)
        return summary

    @staticmethod
    def deployment_report(
        title: str,
        environment: str,
        status: str,
        version: str | None = None,
        url: str | None = None,
    ) -> JobSummary:
        """
        Create a deployment report summary.

        :param title: report title
        :param environment: deployment environment (e.g., 'production', 'staging')
        :param status: deployment status (e.g., 'success', 'failed')
        :param version: optional version string
        :param url: optional deployment URL
        :returns: JobSummary with deployment report
        """
        summary = JobSummary()
        summary.add_heading(title, 1)
        summary.add_separator()

        emoji = "✓" if status.lower() == "success" else "✗"
        summary.add_quote(f"{emoji} Deployment {status}")

        rows = [
            ["Property", "Value"],
            ["Environment", environment],
            ["Status", status],
        ]
        if version:
            rows.append(["Version", version])

        summary.add_table(rows)

        if url:
            summary.add_break()
            summary.add_link(f"View {environment}", url)

        return summary

    @staticmethod
    def benchmark_report(title: str, benchmarks: dict[str, dict[str, str]]) -> JobSummary:
        """
        Create a benchmark report summary.

        :param title: report title
        :param benchmarks: dict mapping benchmark names to metric dicts
        :returns: JobSummary with benchmark report
        """
        summary = JobSummary()
        summary.add_heading(title, 1)
        summary.add_separator()

        if not benchmarks:
            summary.add_raw("No benchmark data available")
            return summary

        for name, metrics in benchmarks.items():
            summary.add_heading(name, 3)
            rows = [["Metric", "Value"]]
            for metric, value in metrics.items():
                rows.append([metric, value])
            summary.add_table(rows)
            summary.add_break()

        return summary
