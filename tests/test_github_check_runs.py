# pyright: reportPrivateUsage=false
# pyright: reportUnusedVariable=false
# pyright: reportUnusedParameter=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false

from __future__ import annotations

import os
from unittest.mock import Mock, patch

import pytest
import requests

from github_action_toolkit.github_check_runs import GitHubCheckRun


@pytest.fixture
def mock_env():
    """Set up environment variables for testing."""
    with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token_123"}):
        yield


@pytest.fixture
def check_run_instance():
    """Create a GitHubCheckRun instance for testing."""
    return GitHubCheckRun(
        repo_owner="test_owner", repo_name="test_repo", sha="abc123", github_token="test_token"
    )


def test_init_with_token():
    """Test initialization with explicit token."""
    check_run = GitHubCheckRun(
        repo_owner="owner", repo_name="repo", sha="sha123", github_token="explicit_token"
    )
    assert check_run.repo_owner == "owner"
    assert check_run.repo_name == "repo"
    assert check_run.sha == "sha123"
    assert check_run.github_token == "explicit_token"


def test_init_with_env_token(mock_env):
    """Test initialization with environment variable token."""
    check_run = GitHubCheckRun(repo_owner="owner", repo_name="repo", sha="sha123")
    assert check_run.github_token == "test_token_123"


def test_init_without_token_warns():
    """Test initialization without token shows warning."""
    with patch.dict(os.environ, {}, clear=True):
        with patch("github_action_toolkit.github_check_runs.gat.warning") as mock_warning:
            check_run = GitHubCheckRun(repo_owner="owner", repo_name="repo", sha="sha123")
            assert check_run.github_token is None
            mock_warning.assert_called_once()


def test_headers_set_correctly():
    """Test that headers are set correctly."""
    check_run = GitHubCheckRun(
        repo_owner="owner", repo_name="repo", sha="sha123", github_token="test_token"
    )
    assert check_run.headers["Authorization"] == "token test_token"
    assert check_run.headers["Accept"] == "application/vnd.github.v3+json"


def test_create_check_run_without_token():
    """Test creating check run without token returns None."""
    with patch.dict(os.environ, {}, clear=True):
        with patch("github_action_toolkit.github_check_runs.gat.warning"):
            check_run = GitHubCheckRun(repo_owner="owner", repo_name="repo", sha="sha123")
            with patch("github_action_toolkit.github_check_runs.gat.warning") as mock_warning:
                result = check_run.create_check_run(name="Test Check")
                assert result is None
                mock_warning.assert_called_once()


def test_create_check_run_basic(check_run_instance):
    """Test creating a basic check run."""
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"id": 123, "name": "Test Check"}

    with patch("requests.post", return_value=mock_response) as mock_post:
        result = check_run_instance.create_check_run(name="Test Check", status="in_progress")

        assert result is not None
        assert result["id"] == 123
        assert result["name"] == "Test Check"

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://api.github.com/repos/test_owner/test_repo/check-runs"
        assert call_args[1]["json"]["name"] == "Test Check"
        assert call_args[1]["json"]["head_sha"] == "abc123"
        assert call_args[1]["json"]["status"] == "in_progress"


def test_create_check_run_completed(check_run_instance):
    """Test creating a completed check run with conclusion."""
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"id": 456, "conclusion": "success"}

    with patch("requests.post", return_value=mock_response) as mock_post:
        result = check_run_instance.create_check_run(
            name="Quality Check", status="completed", conclusion="success"
        )

        assert result is not None
        assert result["conclusion"] == "success"

        call_args = mock_post.call_args
        assert call_args[1]["json"]["status"] == "completed"
        assert call_args[1]["json"]["conclusion"] == "success"


def test_create_check_run_with_output(check_run_instance):
    """Test creating check run with output details."""
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"id": 789}

    with patch("requests.post", return_value=mock_response) as mock_post:
        result = check_run_instance.create_check_run(
            name="Code Quality",
            status="completed",
            conclusion="success",
            title="All checks passed",
            summary="Quality gates passed successfully",
            text="Detailed results here",
        )

        assert result is not None
        call_args = mock_post.call_args
        output = call_args[1]["json"]["output"]
        assert output["title"] == "All checks passed"
        assert output["summary"] == "Quality gates passed successfully"
        assert output["text"] == "Detailed results here"


def test_create_check_run_with_annotations(check_run_instance):
    """Test creating check run with annotations."""
    annotations = [
        {
            "path": "file.py",
            "start_line": 1,
            "end_line": 1,
            "annotation_level": "warning",
            "message": "Test warning",
        }
    ]

    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"id": 999}

    with patch("requests.post", return_value=mock_response) as mock_post:
        result = check_run_instance.create_check_run(
            name="Linter",
            status="completed",
            conclusion="neutral",
            summary="Found some issues",
            annotations=annotations,
        )

        assert result is not None
        call_args = mock_post.call_args
        output = call_args[1]["json"]["output"]
        assert output["annotations"] == annotations


def test_create_check_run_limits_annotations(check_run_instance):
    """Test that annotations are limited to 50."""
    annotations = [{"path": f"file{i}.py", "message": f"Issue {i}"} for i in range(100)]

    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"id": 1000}

    with patch("requests.post", return_value=mock_response) as mock_post:
        result = check_run_instance.create_check_run(
            name="Test", status="completed", summary="Summary", annotations=annotations
        )

        assert result is not None
        call_args = mock_post.call_args
        output = call_args[1]["json"]["output"]
        assert len(output["annotations"]) == 50


def test_create_check_run_http_error(check_run_instance):
    """Test handling HTTP errors."""
    mock_response = Mock()
    mock_response.status_code = 422
    mock_response.text = "Unprocessable Entity"

    with patch("requests.post", return_value=mock_response):
        with patch("github_action_toolkit.github_check_runs.gat.error") as mock_error:
            result = check_run_instance.create_check_run(name="Test Check")
            assert result is None
            mock_error.assert_called_once()


def test_create_check_run_exception(check_run_instance):
    """Test handling exceptions during request."""
    with patch("requests.post", side_effect=requests.exceptions.Timeout("Timeout")):
        with patch("github_action_toolkit.github_check_runs.gat.error") as mock_error:
            result = check_run_instance.create_check_run(name="Test Check")
            assert result is None
            mock_error.assert_called_once()


def test_conclusion_only_added_when_completed(check_run_instance):
    """Test that conclusion is only added when status is completed."""
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"id": 123}

    with patch("requests.post", return_value=mock_response) as mock_post:
        check_run_instance.create_check_run(
            name="Test", status="in_progress", conclusion="success"
        )

        call_args = mock_post.call_args
        assert "conclusion" not in call_args[1]["json"]


def test_api_base_url():
    """Test that API base URL is set correctly."""
    assert GitHubCheckRun.API_BASE == "https://api.github.com"


def test_request_timeout(check_run_instance):
    """Test that requests have a timeout."""
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"id": 123}

    with patch("requests.post", return_value=mock_response) as mock_post:
        check_run_instance.create_check_run(name="Test Check")
        call_args = mock_post.call_args
        assert call_args[1]["timeout"] == 30
