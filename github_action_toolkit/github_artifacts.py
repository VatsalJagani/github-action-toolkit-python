from __future__ import annotations

import hashlib
import os
import time
import zipfile
from pathlib import Path

import requests
from github import Github as PyGithub
from github.Artifact import Artifact
from github.PaginatedList import PaginatedList
from github.Repository import Repository


class GitHubArtifacts:
    """
    Robust artifact management with upload/download, pattern matching,
    integrity checks, and error handling.
    """

    token: str
    action_run_id: str

    def __init__(
        self,
        github_token: str | None = None,
        github_repo: str | None = None,
    ) -> None:
        """
        Initialize GitHubArtifacts with token and repository.

        Args:
            github_token: GitHub token with repo access (optional, defaults to GITHUB_TOKEN env)
            github_repo: Repository in 'owner/repo' format (optional, defaults to GITHUB_REPOSITORY env)
        """
        _token = github_token or os.environ.get("GITHUB_TOKEN")
        if not _token:
            raise ValueError("GitHub token not provided and GITHUB_TOKEN not set in environment.")
        self.token = _token

        if github_repo:
            if "/" not in github_repo:
                raise ValueError("github_repo must be in 'owner/repo' format")
        elif os.environ.get("GITHUB_REPOSITORY"):
            github_repo = os.environ.get("GITHUB_REPOSITORY")
        if not github_repo:
            raise ValueError(
                "GitHub repository not provided and GITHUB_REPOSITORY not set in environment."
            )

        _a_run_id: str | None = os.environ.get("GITHUB_RUN_ID")
        if _a_run_id:
            self.action_run_id = _a_run_id
        else:
            raise RuntimeError("GITHUB_RUN_ID not set")

        gh = PyGithub(login_or_token=self.token)
        self.repo: Repository = gh.get_repo(full_name_or_id=github_repo)

    def get_artifacts(
        self, current_run_only: bool = False, name_pattern: str | None = None
    ) -> PaginatedList[Artifact] | list[Artifact]:
        """
        Get artifacts with optional filtering.

        Args:
            current_run_only: Filter to current workflow run only
            name_pattern: Filter by name pattern (e.g., "test-*" or "*-results")

        Returns:
            List or paginated list of artifacts
        """
        all_artifacts = self.repo.get_artifacts()
        filtered: list[Artifact] = []

        for artifact in all_artifacts:
            if current_run_only and artifact.workflow_run.id != int(self.action_run_id):
                continue
            if name_pattern:
                import fnmatch

                if not fnmatch.fnmatch(artifact.name, name_pattern):
                    continue
            filtered.append(artifact)

        if filtered or current_run_only or name_pattern:
            return filtered
        return all_artifacts

    def get_artifact(self, artifact_id: int) -> Artifact:
        return self.repo.get_artifact(artifact_id=artifact_id)

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _create_zip_from_patterns(
        self, patterns: list[str], artifact_name: str, root_dir: Path | None = None
    ) -> Path:
        """
        Create a zip file from files matching patterns.

        Args:
            patterns: List of glob patterns (e.g., ["*.py", "tests/**/*.py"])
            artifact_name: Name for the artifact
            root_dir: Root directory for pattern matching (defaults to current dir)

        Returns:
            Path to created zip file
        """
        root = root_dir or Path.cwd()
        zip_path = Path(f"{artifact_name}.zip")

        collected_files: set[Path] = set()
        for pattern in patterns:
            matched = root.glob(pattern)
            for file_path in matched:
                if file_path.is_file():
                    collected_files.add(file_path)

        if not collected_files:
            raise ValueError(f"No files matched patterns: {patterns}")

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in sorted(collected_files):
                arcname = file_path.relative_to(root)
                zf.write(file_path, arcname=arcname)

        return zip_path

    def upload_artifact(
        self,
        name: str,
        paths: list[str] | None = None,
        patterns: list[str] | None = None,
        root_dir: str | None = None,
        retention_days: int | None = None,
        verify_checksum: bool = True,
        max_retries: int = 3,
    ) -> dict[str, str]:
        """
        Upload files as an artifact with pattern matching and integrity checks.

        Args:
            name: Artifact name
            paths: List of file/directory paths to include
            patterns: List of glob patterns (e.g., ["*.log", "build/**/*.js"])
            root_dir: Root directory for relative paths (defaults to current dir)
            retention_days: Days to retain artifact (optional)
            verify_checksum: Calculate and store checksum
            max_retries: Maximum retry attempts on failure

        Returns:
            Dictionary with artifact info including checksum

        Example:
            upload_artifact("test-results", patterns=["*.xml", "coverage/**"])
        """
        if not paths and not patterns:
            raise ValueError("Either paths or patterns must be provided")

        root = Path(root_dir) if root_dir else Path.cwd()

        # Collect files from patterns
        all_patterns: list[str] = []
        if patterns:
            all_patterns.extend(patterns)
        if paths:
            all_patterns.extend(paths)

        # Create zip archive
        zip_path = self._create_zip_from_patterns(all_patterns, name, root)

        # Calculate checksum
        checksum = ""
        if verify_checksum:
            checksum = self._calculate_checksum(zip_path)

        # Upload with retry logic
        url = f"https://uploads.github.com/repos/{self.repo.full_name}/actions/artifacts"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
        }

        for attempt in range(max_retries):
            try:
                with open(zip_path, "rb") as f:
                    files = {"file": (f"{name}.zip", f, "application/zip")}
                    data = {"name": name}
                    if retention_days:
                        data["retention_days"] = str(retention_days)

                    response = requests.post(url, headers=headers, files=files, data=data)

                if response.status_code == 201:
                    print(f"Artifact '{name}' uploaded successfully.")
                    result = {
                        "name": name,
                        "size": str(zip_path.stat().st_size),
                        "checksum": checksum,
                    }
                    zip_path.unlink()
                    return result

                if response.status_code >= 500 and attempt < max_retries - 1:
                    wait_time = 2**attempt
                    print(f"Upload failed (attempt {attempt + 1}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                zip_path.unlink()
                raise RuntimeError(
                    f"Failed to upload artifact: {response.status_code} - {response.text}"
                )

            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    print(f"Upload error (attempt {attempt + 1}): {e}, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                zip_path.unlink()
                raise RuntimeError(
                    f"Failed to upload artifact after {max_retries} attempts: {e}"
                ) from e

        zip_path.unlink()
        raise RuntimeError(f"Failed to upload artifact after {max_retries} attempts")

    def download_artifact(
        self,
        artifact: Artifact,
        is_extract: bool = False,
        extract_dir: str | None = None,
        verify_checksum: bool = False,
        expected_checksum: str | None = None,
        max_retries: int = 3,
    ) -> str:
        """
        Download an artifact with optional extraction and integrity verification.

        Args:
            artifact: The artifact object to download
            is_extract: If True, extract the zip contents
            extract_dir: Directory to extract to (defaults to artifact_<name>)
            verify_checksum: Verify file integrity with checksum
            expected_checksum: Expected SHA-256 checksum (if known)
            max_retries: Maximum retry attempts on failure

        Returns:
            Path to downloaded file or extracted directory
        """
        file_name = f"{artifact.name}.zip"

        # Download with retry logic
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    artifact.archive_download_url,
                    headers={"Authorization": f"token {self.token}"},
                    timeout=300,
                )

                if response.status_code == 200:
                    with open(file_name, "wb") as f:
                        f.write(response.content)
                    print(f"Artifact '{artifact.name}' downloaded successfully.")
                    break

                if response.status_code >= 500 and attempt < max_retries - 1:
                    wait_time = 2**attempt
                    print(f"Download failed (attempt {attempt + 1}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                raise RuntimeError(
                    f"Failed to download artifact: {response.status_code} - {response.text}"
                )

            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    print(
                        f"Download error (attempt {attempt + 1}): {e}, retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                    continue
                raise RuntimeError(
                    f"Failed to download artifact after {max_retries} attempts: {e}"
                ) from e

        # Verify checksum if requested
        if verify_checksum or expected_checksum:
            file_path = Path(file_name)
            actual_checksum = self._calculate_checksum(file_path)
            if expected_checksum and actual_checksum != expected_checksum:
                file_path.unlink()
                raise ValueError(
                    f"Checksum mismatch: expected {expected_checksum}, got {actual_checksum}"
                )
            print(f"Checksum verified: {actual_checksum}")

        if is_extract:
            dir_path: str = extract_dir or f"artifact_{artifact.name}"
            with zipfile.ZipFile(file_name, "r") as z:
                z.extractall(dir_path)
            os.remove(file_name)
            return dir_path
        return file_name

    def delete_artifact(self, artifact: Artifact, max_retries: int = 3) -> bool:
        """
        Delete an artifact with retry logic.

        Args:
            artifact: The artifact object to delete
            max_retries: Maximum retry attempts on failure

        Returns:
            True if deleted successfully, False otherwise
        """
        headers: dict[str, str] = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
        }
        url = f"https://api.github.com/repos/{self.repo.full_name}/actions/artifacts/{artifact.id}"

        for attempt in range(max_retries):
            try:
                response = requests.delete(url, headers=headers, timeout=30)

                if response.status_code == 204:
                    print(f"Artifact {artifact.id} ({artifact.name}) deleted successfully.")
                    return True

                if response.status_code >= 500 and attempt < max_retries - 1:
                    wait_time = 2**attempt
                    print(f"Delete failed (attempt {attempt + 1}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                print(
                    f"Failed to delete artifact {artifact.id} ({artifact.name}): "
                    f"{response.status_code}"
                )
                return False

            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    print(f"Delete error (attempt {attempt + 1}): {e}, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                print(f"Failed to delete artifact after {max_retries} attempts: {e}")
                return False

        return False
