# pyright: reportPrivateUsage=false
# pyright: reportUnusedVariable=false
# pyright: reportUnusedParameter=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUnknownMemberType=false

import os
import re
from pathlib import Path
from typing import Any

import pytest

import github_action_toolkit.debugging as gat_debugging


@pytest.fixture
def temp_directory(tmp_path: Path) -> Path:
    """Create a temporary directory with a known structure for testing."""
    # Directories
    for dir_path in ["subdir1", "subdir2", "subdir2/nested"]:
        (tmp_path / dir_path).mkdir(parents=True)
    # Files at root
    for f in ["file1.txt", "file2.txt"]:
        (tmp_path / f).touch()
    # Files in subdirs
    for f in ["sub1_file1.txt", "sub1_file2.txt"]:
        (tmp_path / "subdir1" / f).touch()
    (tmp_path / "subdir2" / "sub2_file1.txt").touch()
    (tmp_path / "subdir2" / "nested" / "deep_file.txt").touch()
    return tmp_path


def _filtered_lines(out: str) -> list[str]:
    """Return non-empty, non-group lines, right-stripped."""
    return [
        line.rstrip()
        for line in out.splitlines()
        if line.strip() and "::group" not in line and "::endgroup" not in line
    ]


@pytest.mark.parametrize(
    "max_level, expected_patterns",
    [
        # Level 0: root + root files only
        (
            0,
            [
                r"^[^/]+/$",
                r"^├── file1\.txt$",
                r"^├── file2\.txt$",
            ],
        ),
        # Level 1: includes first-level dirs and their files
        (
            1,
            [
                r"^[^/]+/$",
                r"^├── file1\.txt$",
                r"^├── file2\.txt$",
                r"^├── subdir1/$",
                r"^│\s{3}├── sub1_file1\.txt$",
                r"^│\s{3}└── sub1_file2\.txt$",
                r"^└── subdir2/$",
                r"^│\s{3}├── sub2_file1\.txt$",
            ],
        ),
        # Level 2: includes nested directory and deep file
        (
            2,
            [
                r"^[^/]+/$",
                r"^├── file1\.txt$",
                r"^├── file2\.txt$",
                r"^├── subdir1/$",
                r"^│\s{3}├── sub1_file1\.txt$",
                r"^│\s{3}└── sub1_file2\.txt$",
                r"^└── subdir2/$",
                r"^│\s{3}├── sub2_file1\.txt$",
                r"^│\s{3}├── nested/$",
                r"^│\s{3}│\s{3}└── deep_file\.txt$",
            ],
        ),
        # Level 3: same as level 2 for this structure
        (
            3,
            [
                r"^[^/]+/$",
                r"^├── file1\.txt$",
                r"^├── file2\.txt$",
                r"^├── subdir1/$",
                r"^│\s{3}├── sub1_file1\.txt$",
                r"^│\s{3}└── sub1_file2\.txt$",
                r"^└── subdir2/$",
                r"^│\s{3}├── sub2_file1\.txt$",
                r"^│\s{3}├── nested/$",
                r"^│\s{3}│\s{3}└── deep_file\.txt$",
            ],
        ),
    ],
)
def test_print_directory_tree(
    capfd: Any, temp_directory: Path, max_level: int, expected_patterns: list[str]
) -> None:
    original_dir = os.getcwd()
    os.chdir(temp_directory)
    try:
        gat_debugging.print_directory_tree(max_level=max_level)
        out, _ = capfd.readouterr()
        lines = _filtered_lines(out)

        # Basic root line checks
        assert lines, "No output captured"
        assert lines[0].endswith("/") and "──" not in lines[0]

        # Count must match patterns exactly for stability
        assert len(lines) == len(expected_patterns), (
            f"Line count mismatch for max_level={max_level}.\n"
            f"Expected {len(expected_patterns)} lines, got {len(lines)}.\n"
            f"Lines: {lines}"
        )

        # Match each line against expected pattern
        for line, pattern in zip(lines, expected_patterns, strict=False):
            assert re.match(pattern, line), f"Line {line!r} does not match {pattern!r}"

        # Negative assertions by level
        if max_level <= 1:
            assert all("deep_file.txt" not in _l for _l in lines)
        if max_level == 0:
            assert all("subdir" not in _l for _l in lines)
    finally:
        os.chdir(original_dir)


def test_print_directory_tree_empty_dir(capfd: Any, tmp_path: Path) -> None:
    original_dir = os.getcwd()
    os.chdir(tmp_path)
    try:
        gat_debugging.print_directory_tree()
        out, _ = capfd.readouterr()
        lines = _filtered_lines(out)
        assert len(lines) == 1
        assert lines[0].endswith("/")
        assert "──" not in lines[0]
    finally:
        os.chdir(original_dir)
