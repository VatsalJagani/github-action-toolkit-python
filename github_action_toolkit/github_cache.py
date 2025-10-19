from __future__ import annotations

import hashlib
import os
import tarfile
import tempfile
from pathlib import Path

import requests

from .exceptions import CacheNotFoundError, CacheRestoreError, CacheSaveError


class GitHubCache:
    """
    GitHub Actions cache client for saving and restoring cache with composite keys.

    Provides performance optimizations through caching across workflow runs,
    supporting hierarchical key fallbacks and cross-job data sharing.
    """

    def __init__(
        self,
        github_token: str | None = None,
        github_repo: str | None = None,
    ) -> None:
        """
        Initialize cache client.

        Args:
            github_token: GitHub token with repo access (defaults to GITHUB_TOKEN env var)
            github_repo: Repository in 'owner/repo' format (defaults to GITHUB_REPOSITORY env var)
        """
        _token = github_token or os.environ.get("GITHUB_TOKEN")
        if not _token:
            raise ValueError("GitHub token not provided and GITHUB_TOKEN not set in environment.")
        self.token: str = _token

        if github_repo:
            if "/" not in github_repo:
                raise ValueError("github_repo must be in 'owner/repo' format")
        elif os.environ.get("GITHUB_REPOSITORY"):
            github_repo = os.environ.get("GITHUB_REPOSITORY")
        if not github_repo:
            raise ValueError(
                "GitHub repository not provided and GITHUB_REPOSITORY not set in environment."
            )
        self.repo: str = github_repo

        # Get workflow run ID for cache scope
        self.run_id: str | None = os.environ.get("GITHUB_RUN_ID")
        if not self.run_id:
            raise RuntimeError("GITHUB_RUN_ID not set")

        self.api_url: str = os.environ.get("ACTIONS_CACHE_URL") or "https://api.github.com"
        self.api_version: str = "6.0-preview.1"

    def _get_cache_version(self, paths: list[str | Path]) -> str:
        """
        Generate a cache version hash from paths.

        Used to invalidate cache when path structure changes.
        """
        path_str = "\n".join(sorted(str(p) for p in paths))
        return hashlib.sha256(path_str.encode()).hexdigest()[:8]

    def _get_headers(self) -> dict[str, str]:
        """Get headers for API requests."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        }

    def _compress_paths(self, paths: list[str | Path], archive_path: Path) -> int:
        """
        Compress paths into a tar.gz archive.

        Returns the size of the archive in bytes.
        """
        with tarfile.open(archive_path, "w:gz") as tar:
            for path in paths:
                path = Path(path)
                if not path.exists():
                    raise FileNotFoundError(f"Path does not exist: {path}")
                tar.add(path, arcname=path.name)
        return archive_path.stat().st_size

    def _decompress_archive(self, archive_path: Path, target_dir: Path) -> None:
        """Decompress a tar.gz archive to target directory."""
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(target_dir)

    def save_cache(
        self,
        paths: list[str | Path],
        key: str,
        enable_cross_os_archive: bool = False,  # pyright: ignore[reportUnusedParameter]
    ) -> int | None:
        """
        Save cache with the specified key.

        Args:
            paths: List of file/directory paths to cache
            key: Primary cache key (can include variables like version, hash)
            enable_cross_os_archive: Enable cross-OS compatibility (default: False)

        Returns:
            Cache ID if successful, None otherwise

        Example:
            ```python
            cache = GitHubCache()
            paths = ["node_modules", ".cache"]
            key = f"npm-{platform}-{hash_of_package_lock}"
            cache_id = cache.save_cache(paths, key)
            ```
        """
        if not paths:
            raise ValueError("At least one path must be specified")

        if not key:
            raise ValueError("Cache key must be specified")

        # Generate cache version
        version = self._get_cache_version(paths)

        # Create temporary archive
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = Path(tmpdir) / "cache.tgz"

            try:
                archive_size = self._compress_paths(paths, archive_path)
            except Exception as e:
                raise CacheSaveError(f"Failed to compress paths: {e}") from e

            # Reserve cache entry
            reserve_url = f"{self.api_url}/repos/{self.repo}/actions/cache"
            reserve_data = {
                "key": key,
                "version": version,
            }

            try:
                response = requests.post(
                    reserve_url,
                    headers=self._get_headers(),
                    json=reserve_data,
                    timeout=30,
                )

                if response.status_code == 409:
                    # Cache already exists
                    return None

                response.raise_for_status()
                cache_id = response.json().get("cacheId")

                # Upload cache
                upload_url = f"{self.api_url}/repos/{self.repo}/actions/cache/{cache_id}"

                with open(archive_path, "rb") as f:
                    upload_response = requests.patch(
                        upload_url,
                        headers={
                            **self._get_headers(),
                            "Content-Type": "application/octet-stream",
                            "Content-Range": f"bytes 0-{archive_size - 1}/*",
                        },
                        data=f,
                        timeout=300,
                    )
                    upload_response.raise_for_status()

                # Commit the cache
                commit_url = f"{self.api_url}/repos/{self.repo}/actions/cache/{cache_id}"
                commit_response = requests.post(
                    commit_url,
                    headers=self._get_headers(),
                    json={"size": archive_size},
                    timeout=30,
                )
                commit_response.raise_for_status()

                return cache_id

            except requests.RequestException as e:
                raise CacheSaveError(f"Failed to save cache: {e}") from e

    def restore_cache(
        self,
        paths: list[str | Path],
        primary_key: str,
        restore_keys: list[str] | None = None,
        enable_cross_os_archive: bool = False,  # pyright: ignore[reportUnusedParameter]
    ) -> str | None:
        """
        Restore cache with fallback key hierarchy.

        Args:
            paths: List of file/directory paths to restore
            primary_key: Primary cache key to look for
            restore_keys: Fallback keys to try if primary key not found
            enable_cross_os_archive: Enable cross-OS compatibility (default: False)

        Returns:
            The matched cache key if found and restored, None otherwise

        Example:
            ```python
            cache = GitHubCache()
            paths = ["node_modules"]
            primary = f"npm-{platform}-{hash_of_lockfile}"
            fallbacks = [f"npm-{platform}-", "npm-"]

            matched_key = cache.restore_cache(paths, primary, fallbacks)
            if matched_key:
                print(f"Cache restored from key: {matched_key}")
            ```
        """
        if not paths:
            raise ValueError("At least one path must be specified")

        if not primary_key:
            raise ValueError("Primary key must be specified")

        # Generate cache version
        version = self._get_cache_version(paths)

        # Build list of keys to try
        keys_to_try = [primary_key]
        if restore_keys:
            keys_to_try.extend(restore_keys)

        # Try each key
        for key in keys_to_try:
            try:
                # Query cache
                query_url = f"{self.api_url}/repos/{self.repo}/actions/cache"
                params = {
                    "keys": key,
                    "version": version,
                }

                response = requests.get(
                    query_url,
                    headers=self._get_headers(),
                    params=params,
                    timeout=30,
                )

                if response.status_code == 204:
                    # No cache found for this key
                    continue

                response.raise_for_status()
                cache_entry = response.json()

                # Download cache
                archive_url = cache_entry.get("archiveLocation")
                if not archive_url:
                    continue

                with tempfile.TemporaryDirectory() as tmpdir:
                    archive_path = Path(tmpdir) / "cache.tgz"

                    # Download archive
                    download_response = requests.get(archive_url, timeout=300)
                    download_response.raise_for_status()

                    with open(archive_path, "wb") as f:
                        f.write(download_response.content)

                    # Extract to first path's parent directory or current directory
                    if paths:
                        first_path = Path(paths[0])
                        if first_path.is_absolute():
                            target_dir = first_path.parent if first_path.is_file() else first_path
                        else:
                            target_dir = Path.cwd()
                    else:
                        target_dir = Path.cwd()
                    self._decompress_archive(archive_path, target_dir)

                return cache_entry.get("cacheKey", key)

            except requests.RequestException:
                # Continue to next key on error
                continue

        return None

    def is_feature_available(self) -> bool:
        """
        Check if cache feature is available in the current environment.

        Returns:
            True if cache is available, False otherwise
        """
        return bool(os.environ.get("ACTIONS_CACHE_URL") or os.environ.get("ACTIONS_RUNTIME_TOKEN"))


__all__ = ["GitHubCache", "CacheNotFoundError", "CacheRestoreError", "CacheSaveError"]
