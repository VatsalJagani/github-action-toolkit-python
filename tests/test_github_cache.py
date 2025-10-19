# pyright: reportPrivateUsage=false
# pyright: reportUnusedVariable=false
# pyright: reportUnusedParameter=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUnknownMemberType=false

import tarfile
import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest import mock

import pytest

from github_action_toolkit.github_cache import (
    GitHubCache,
)


@pytest.fixture
def mock_env(monkeypatch):
    """Set up environment variables for cache testing."""
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("GITHUB_RUN_ID", "123456")
    monkeypatch.setenv("ACTIONS_CACHE_URL", "https://api.github.com")


@pytest.fixture
def temp_cache_paths() -> Generator[list[Path], None, None]:
    """Create temporary files/directories for cache testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create test files
        file1 = tmpdir_path / "file1.txt"
        file1.write_text("content1")

        dir1 = tmpdir_path / "dir1"
        dir1.mkdir()
        (dir1 / "nested.txt").write_text("nested content")

        yield [file1, dir1]


def test_init_with_env(mock_env):
    """Test GitHubCache initialization with environment variables."""
    cache = GitHubCache()
    assert cache.token == "fake-token"
    assert cache.repo == "owner/repo"
    assert cache.run_id == "123456"


def test_init_without_token(monkeypatch):
    """Test initialization fails without token."""
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("GITHUB_RUN_ID", "123456")

    with pytest.raises(ValueError, match="GitHub token not provided"):
        GitHubCache()


def test_init_without_repo(monkeypatch):
    """Test initialization fails without repository."""
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    monkeypatch.setenv("GITHUB_RUN_ID", "123456")

    with pytest.raises(ValueError, match="GitHub repository not provided"):
        GitHubCache()


def test_init_without_run_id(monkeypatch):
    """Test initialization fails without run ID."""
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.delenv("GITHUB_RUN_ID", raising=False)

    with pytest.raises(RuntimeError, match="GITHUB_RUN_ID not set"):
        GitHubCache()


def test_init_with_invalid_repo_format(monkeypatch):
    """Test initialization fails with invalid repo format."""
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    monkeypatch.setenv("GITHUB_RUN_ID", "123456")

    with pytest.raises(ValueError, match="must be in 'owner/repo' format"):
        GitHubCache(github_repo="invalid-repo")


def test_get_cache_version(mock_env):
    """Test cache version generation."""
    cache = GitHubCache()
    paths: list[str | Path] = [Path("/path/to/file1"), Path("/path/to/file2")]
    version1 = cache._get_cache_version(paths)

    # Same paths should give same version
    version2 = cache._get_cache_version(paths)
    assert version1 == version2

    # Different paths should give different version
    paths2: list[str | Path] = [Path("/path/to/file3")]
    version3 = cache._get_cache_version(paths2)
    assert version1 != version3


def test_compress_and_decompress(mock_env, temp_cache_paths):
    """Test compression and decompression of paths."""
    cache = GitHubCache()

    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = Path(tmpdir) / "test.tgz"

        # Compress
        paths: list[str | Path] = temp_cache_paths
        size = cache._compress_paths(paths, archive_path)  # pyright: ignore[reportUnknownArgumentType]
        assert size > 0
        assert archive_path.exists()

        # Decompress
        extract_dir = Path(tmpdir) / "extract"
        extract_dir.mkdir()
        cache._decompress_archive(archive_path, extract_dir)

        # Verify extracted files
        assert (extract_dir / "file1.txt").exists()
        assert (extract_dir / "dir1").is_dir()
        assert (extract_dir / "dir1" / "nested.txt").exists()


def test_compress_nonexistent_path(mock_env):
    """Test compression fails with nonexistent path."""
    cache = GitHubCache()

    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = Path(tmpdir) / "test.tgz"
        paths: list[str | Path] = [Path("/nonexistent/path")]

        with pytest.raises(FileNotFoundError):
            cache._compress_paths(paths, archive_path)


@mock.patch("github_action_toolkit.github_cache.requests.post")
@mock.patch("github_action_toolkit.github_cache.requests.patch")
def test_save_cache_success(mock_patch, mock_post, mock_env, temp_cache_paths):
    """Test successful cache save."""
    cache = GitHubCache()

    # Mock reserve response
    mock_reserve_response = mock.Mock()
    mock_reserve_response.status_code = 200
    mock_reserve_response.json.return_value = {"cacheId": 123}

    # Mock upload response
    mock_upload_response = mock.Mock()
    mock_upload_response.status_code = 200

    # Mock commit response
    mock_commit_response = mock.Mock()
    mock_commit_response.status_code = 200

    mock_post.side_effect = [mock_reserve_response, mock_commit_response]
    mock_patch.return_value = mock_upload_response

    paths: list[str | Path] = temp_cache_paths
    cache_id = cache.save_cache(paths, "test-key")  # pyright: ignore[reportUnknownArgumentType]
    assert cache_id == 123


@mock.patch("github_action_toolkit.github_cache.requests.post")
def test_save_cache_already_exists(mock_post, mock_env, temp_cache_paths):
    """Test cache save when cache already exists."""
    cache = GitHubCache()

    # Mock response indicating cache exists
    mock_response = mock.Mock()
    mock_response.status_code = 409
    mock_post.return_value = mock_response

    paths: list[str | Path] = temp_cache_paths
    cache_id = cache.save_cache(paths, "existing-key")  # pyright: ignore[reportUnknownArgumentType]
    assert cache_id is None


def test_save_cache_empty_paths(mock_env):
    """Test save cache fails with empty paths."""
    cache = GitHubCache()

    with pytest.raises(ValueError, match="At least one path must be specified"):
        cache.save_cache([], "test-key")


def test_save_cache_empty_key(mock_env, temp_cache_paths):
    """Test save cache fails with empty key."""
    cache = GitHubCache()

    with pytest.raises(ValueError, match="Cache key must be specified"):
        paths: list[str | Path] = temp_cache_paths
        cache.save_cache(paths, "")  # pyright: ignore[reportUnknownArgumentType]


@mock.patch("github_action_toolkit.github_cache.requests.get")
def test_restore_cache_success(mock_get, mock_env, temp_cache_paths):
    """Test successful cache restore."""
    cache = GitHubCache()

    # Create a test archive
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = Path(tmpdir) / "cache.tgz"
        with tarfile.open(archive_path, "w:gz") as tar:
            for path in temp_cache_paths:
                tar.add(str(path), arcname=path.name)  # pyright: ignore[reportUnknownArgumentType]

        # Mock query response
        mock_query_response = mock.Mock()
        mock_query_response.status_code = 200
        mock_query_response.json.return_value = {
            "cacheKey": "test-key",
            "archiveLocation": "https://example.com/cache.tgz",
        }

        # Mock download response
        mock_download_response = mock.Mock()
        mock_download_response.status_code = 200
        with open(archive_path, "rb") as f:
            mock_download_response.content = f.read()

        mock_get.side_effect = [mock_query_response, mock_download_response]

        # Use temporary directory for restore target
        restore_dir = Path(tmpdir) / "restore"
        restore_dir.mkdir()
        matched_key = cache.restore_cache([restore_dir], "test-key")
        assert matched_key == "test-key"


@mock.patch("github_action_toolkit.github_cache.requests.get")
def test_restore_cache_with_fallback(mock_get, mock_env, temp_cache_paths):
    """Test cache restore with fallback keys."""
    cache = GitHubCache()

    # First key not found
    mock_not_found = mock.Mock()
    mock_not_found.status_code = 204

    # Second key found
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = Path(tmpdir) / "cache.tgz"
        with tarfile.open(archive_path, "w:gz") as tar:
            for path in temp_cache_paths:
                tar.add(str(path), arcname=path.name)  # pyright: ignore[reportUnknownArgumentType]

        mock_found_response = mock.Mock()
        mock_found_response.status_code = 200
        mock_found_response.json.return_value = {
            "cacheKey": "fallback-key",
            "archiveLocation": "https://example.com/cache.tgz",
        }

        mock_download_response = mock.Mock()
        mock_download_response.status_code = 200
        with open(archive_path, "rb") as f:
            mock_download_response.content = f.read()

        mock_get.side_effect = [mock_not_found, mock_found_response, mock_download_response]

        # Use temporary directory for restore target
        restore_dir = Path(tmpdir) / "restore"
        restore_dir.mkdir()
        matched_key = cache.restore_cache(
            [restore_dir], "primary-key", restore_keys=["fallback-key"]
        )
        assert matched_key == "fallback-key"


@mock.patch("github_action_toolkit.github_cache.requests.get")
def test_restore_cache_not_found(mock_get, mock_env):
    """Test cache restore when no cache found."""
    cache = GitHubCache()

    mock_response = mock.Mock()
    mock_response.status_code = 204
    mock_get.return_value = mock_response

    with tempfile.TemporaryDirectory() as tmpdir:
        restore_dir = Path(tmpdir) / "restore"
        restore_dir.mkdir()
        matched_key = cache.restore_cache([restore_dir], "nonexistent-key")
        assert matched_key is None


def test_restore_cache_empty_paths(mock_env):
    """Test restore cache fails with empty paths."""
    cache = GitHubCache()

    with pytest.raises(ValueError, match="At least one path must be specified"):
        cache.restore_cache([], "test-key")


def test_restore_cache_empty_key(mock_env):
    """Test restore cache fails with empty key."""
    cache = GitHubCache()

    with pytest.raises(ValueError, match="Primary key must be specified"):
        cache.restore_cache([Path(".")], "")


def test_is_feature_available(mock_env):
    """Test cache feature availability check."""
    cache = GitHubCache()
    assert cache.is_feature_available() is True


def test_is_feature_available_no_cache_url(monkeypatch):
    """Test cache feature availability without cache URL."""
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("GITHUB_RUN_ID", "123456")
    monkeypatch.delenv("ACTIONS_CACHE_URL", raising=False)
    monkeypatch.delenv("ACTIONS_RUNTIME_TOKEN", raising=False)

    cache = GitHubCache()
    assert cache.is_feature_available() is False
