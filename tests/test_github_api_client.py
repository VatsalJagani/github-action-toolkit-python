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
import time
from unittest.mock import Mock, patch

import pytest
from github import GithubException

from github_action_toolkit.github_api_client import (
    APIError,
    GitHubAPIClient,
    RateLimitError,
)


@pytest.fixture
def mock_env():
    """Set up environment variables for testing."""
    with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token_123"}):
        yield


@pytest.fixture
def mock_pygithub():
    """Mock PyGithub instance."""
    with patch("github_action_toolkit.github_api_client.PyGithub") as mock:
        yield mock


def test_init_with_token():
    """Test initialization with explicit token."""
    client = GitHubAPIClient(token="explicit_token")
    assert client.token == "explicit_token"
    assert client.base_url == "https://api.github.com"


def test_init_with_env_token(mock_env):
    """Test initialization with environment variable token."""
    client = GitHubAPIClient()
    assert client.token == "test_token_123"


def test_init_without_token():
    """Test initialization fails without token."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="GitHub token is required"):
            GitHubAPIClient()


def test_init_with_custom_base_url(mock_pygithub):
    """Test initialization with custom base URL for GHES."""
    client = GitHubAPIClient(
        token="test_token", api_base_url="https://github.enterprise.com/api/v3"
    )
    assert client.base_url == "https://github.enterprise.com/api/v3"
    mock_pygithub.assert_called_once()


def test_session_creation():
    """Test that session is created with retry logic."""
    client = GitHubAPIClient(token="test_token")
    assert client._session is not None
    assert hasattr(client._session, "adapters")


def test_get_repository(mock_pygithub):
    """Test getting a repository."""
    mock_repo = Mock()
    mock_github_instance = Mock()
    mock_github_instance.get_repo.return_value = mock_repo
    mock_pygithub.return_value = mock_github_instance

    client = GitHubAPIClient(token="test_token")
    repo = client.get_repository("owner/repo")

    assert repo == mock_repo
    mock_github_instance.get_repo.assert_called_once_with(full_name_or_id="owner/repo")


def test_get_user_authenticated(mock_pygithub):
    """Test getting the authenticated user."""
    mock_user = Mock()
    mock_github_instance = Mock()
    mock_github_instance.get_user.return_value = mock_user
    mock_pygithub.return_value = mock_github_instance

    client = GitHubAPIClient(token="test_token")
    user = client.get_user()

    assert user == mock_user
    mock_github_instance.get_user.assert_called_once_with()


def test_get_user_by_login(mock_pygithub):
    """Test getting a user by login."""
    mock_user = Mock()
    mock_github_instance = Mock()
    mock_github_instance.get_user.return_value = mock_user
    mock_pygithub.return_value = mock_github_instance

    client = GitHubAPIClient(token="test_token")
    user = client.get_user("octocat")

    assert user == mock_user
    mock_github_instance.get_user.assert_called_once_with(login="octocat")


def test_get_organization(mock_pygithub):
    """Test getting an organization."""
    mock_org = Mock()
    mock_github_instance = Mock()
    mock_github_instance.get_organization.return_value = mock_org
    mock_pygithub.return_value = mock_github_instance

    client = GitHubAPIClient(token="test_token")
    org = client.get_organization("github")

    assert org == mock_org
    mock_github_instance.get_organization.assert_called_once_with("github")


def test_paginate_with_list(mock_pygithub):
    """Test pagination with a paginated list."""
    mock_items = [Mock(), Mock(), Mock()]

    # Create a mock that is properly iterable
    mock_paginated_list = mock_items  # Just use the list directly

    mock_github_instance = Mock()
    mock_pygithub.return_value = mock_github_instance

    client = GitHubAPIClient(token="test_token")
    items = list(client.paginate(mock_paginated_list))  # pyright: ignore[reportArgumentType]

    assert len(items) == 3
    assert items == mock_items


def test_paginate_with_callable(mock_pygithub):
    """Test pagination with a callable that returns a paginated list."""
    mock_items = [Mock(), Mock()]
    mock_paginated_list = Mock()
    mock_paginated_list.__iter__ = Mock(return_value=iter(mock_items))

    def get_issues():
        return mock_paginated_list

    mock_github_instance = Mock()
    mock_pygithub.return_value = mock_github_instance

    client = GitHubAPIClient(token="test_token")
    items = list(client.paginate(get_issues))

    assert len(items) == 2


def test_request_success():
    """Test successful HTTP request."""
    client = GitHubAPIClient(token="test_token")

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {}
    mock_response.json.return_value = {"key": "value"}

    with patch.object(client._session, "request", return_value=mock_response):
        response = client.request("GET", "/user")

    assert response.status_code == 200
    assert response.json() == {"key": "value"}


def test_request_with_relative_url():
    """Test request with relative URL."""
    client = GitHubAPIClient(token="test_token")

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {}

    with patch.object(client._session, "request", return_value=mock_response) as mock_req:
        client.request("GET", "user/repos")

    # Check that URL was properly constructed
    call_args = mock_req.call_args
    assert call_args[0][1] == "https://api.github.com/user/repos"


def test_request_rate_limit_with_wait():
    """Test rate limit handling with automatic waiting."""
    client = GitHubAPIClient(token="test_token", rate_limit_wait=True)

    reset_time = int(time.time()) + 2
    mock_response_rate_limited = Mock()
    mock_response_rate_limited.status_code = 403
    mock_response_rate_limited.headers = {
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": str(reset_time),
    }

    mock_response_success = Mock()
    mock_response_success.status_code = 200
    mock_response_success.headers = {}

    with patch.object(
        client._session,
        "request",
        side_effect=[mock_response_rate_limited, mock_response_success],
    ):
        with patch.object(time, "sleep") as mock_sleep:
            response = client.request("GET", "/user")

    assert response.status_code == 200
    assert mock_sleep.called


def test_request_rate_limit_without_wait():
    """Test rate limit handling without automatic waiting."""
    client = GitHubAPIClient(token="test_token", rate_limit_wait=False)

    reset_time = int(time.time()) + 60
    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.headers = {
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": str(reset_time),
    }

    with patch.object(client._session, "request", return_value=mock_response):
        with pytest.raises(RateLimitError):
            client.request("GET", "/user")


def test_request_with_etag():
    """Test conditional requests with ETag."""
    client = GitHubAPIClient(token="test_token")

    # First request - get ETag
    mock_response1 = Mock()
    mock_response1.status_code = 200
    mock_response1.headers = {"ETag": '"abc123"'}
    mock_response1.json.return_value = {"data": "value1"}

    # Second request - 304 Not Modified
    mock_response2 = Mock()
    mock_response2.status_code = 304
    mock_response2.headers = {}

    with patch.object(
        client._session, "request", side_effect=[mock_response1, mock_response2]
    ) as mock_req:
        response1 = client.request("GET", "/data", use_etag=True)
        response2 = client.request("GET", "/data", use_etag=True)

    assert response1.json() == {"data": "value1"}
    assert response2.json() == {"data": "value1"}  # Cached response

    # Check that second request included If-None-Match header
    second_call_headers = mock_req.call_args_list[1][1]["headers"]
    assert second_call_headers["If-None-Match"] == '"abc123"'


def test_request_error():
    """Test handling of API errors."""
    client = GitHubAPIClient(token="test_token")

    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    mock_response.json.return_value = {"message": "Repository not found"}

    with patch.object(client._session, "request", return_value=mock_response):
        with pytest.raises(APIError) as exc_info:
            client.request("GET", "/repos/nonexistent/repo")

    assert exc_info.value.status_code == 404
    assert "Repository not found" in str(exc_info.value)


def test_graphql_success():
    """Test successful GraphQL query."""
    client = GitHubAPIClient(token="test_token")

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": {"viewer": {"login": "octocat"}}}

    with patch.object(client._session, "request", return_value=mock_response):
        result = client.graphql("query { viewer { login } }")

    assert result == {"viewer": {"login": "octocat"}}


def test_graphql_with_variables():
    """Test GraphQL query with variables."""
    client = GitHubAPIClient(token="test_token")

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": {"repository": {"name": "test"}}}

    with patch.object(client._session, "request", return_value=mock_response) as mock_req:
        result = client.graphql(
            "query($owner: String!) { repository(owner: $owner) { name } }",
            variables={"owner": "github"},
        )

    assert result == {"repository": {"name": "test"}}

    # Verify variables were sent
    call_json = mock_req.call_args[1]["json"]
    assert call_json["variables"] == {"owner": "github"}


def test_graphql_error():
    """Test GraphQL query with errors."""
    client = GitHubAPIClient(token="test_token")

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "errors": [{"message": "Field 'invalid' doesn't exist on type 'Query'"}]
    }

    with patch.object(client._session, "request", return_value=mock_response):
        with pytest.raises(APIError) as exc_info:
            client.graphql("query { invalid }")

    assert "Field 'invalid' doesn't exist" in str(exc_info.value)


def test_get_rate_limit(mock_pygithub):
    """Test getting rate limit information."""
    mock_rate_limit = Mock()
    mock_core = Mock()
    mock_core.limit = 5000
    mock_core.remaining = 4999
    mock_core.reset.timestamp.return_value = 1234567890.0
    mock_rate_limit.core = mock_core

    mock_search = Mock()
    mock_search.limit = 30
    mock_search.remaining = 29
    mock_search.reset.timestamp.return_value = 1234567890.0
    mock_rate_limit.search = mock_search

    mock_graphql = Mock()
    mock_graphql.limit = 5000
    mock_graphql.remaining = 4999
    mock_graphql.reset.timestamp.return_value = 1234567890.0
    mock_rate_limit.graphql = mock_graphql

    mock_github_instance = Mock()
    mock_github_instance.get_rate_limit.return_value = mock_rate_limit
    mock_pygithub.return_value = mock_github_instance

    client = GitHubAPIClient(token="test_token")
    rate_limit_info = client.get_rate_limit()

    assert rate_limit_info["core"]["limit"] == 5000
    assert rate_limit_info["core"]["remaining"] == 4999
    assert rate_limit_info["search"]["limit"] == 30
    assert rate_limit_info["graphql"]["limit"] == 5000


def test_with_rate_limit_handling_github_exception(mock_pygithub):
    """Test rate limit handling with GithubException."""
    mock_github_instance = Mock()

    # Create a GithubException for rate limiting
    rate_limit_exception = GithubException(
        status=403,
        data={"message": "API rate limit exceeded"},
        headers={},
    )

    mock_rate_limit = Mock()
    mock_core = Mock()
    mock_core.reset.timestamp.return_value = time.time() + 1
    mock_rate_limit.core = mock_core
    mock_github_instance.get_rate_limit.return_value = mock_rate_limit

    # First call raises exception, second succeeds
    mock_repo = Mock()
    mock_github_instance.get_repo.side_effect = [rate_limit_exception, mock_repo]

    mock_pygithub.return_value = mock_github_instance

    client = GitHubAPIClient(token="test_token", rate_limit_wait=True)

    with patch.object(time, "sleep"):
        repo = client.get_repository("owner/repo")

    assert repo == mock_repo


def test_with_rate_limit_handling_no_wait(mock_pygithub):
    """Test rate limit handling without waiting."""
    mock_github_instance = Mock()

    rate_limit_exception = GithubException(
        status=403,
        data={"message": "API rate limit exceeded"},
        headers={},
    )
    mock_github_instance.get_repo.side_effect = rate_limit_exception

    mock_pygithub.return_value = mock_github_instance

    client = GitHubAPIClient(token="test_token", rate_limit_wait=False)

    with pytest.raises(RateLimitError):
        client.get_repository("owner/repo")


def test_with_rate_limit_handling_non_rate_limit_error(mock_pygithub):
    """Test handling of non-rate-limit GithubException."""
    mock_github_instance = Mock()

    not_found_exception = GithubException(
        status=404,
        data={"message": "Not Found"},
        headers={},
    )
    mock_github_instance.get_repo.side_effect = not_found_exception

    mock_pygithub.return_value = mock_github_instance

    client = GitHubAPIClient(token="test_token")

    with pytest.raises(APIError) as exc_info:
        client.get_repository("owner/nonexistent")

    assert exc_info.value.status_code == 404


def test_github_property(mock_pygithub):
    """Test accessing the underlying PyGithub instance."""
    mock_github_instance = Mock()
    mock_pygithub.return_value = mock_github_instance

    client = GitHubAPIClient(token="test_token")
    assert client.github == mock_github_instance


## Tests


def test_api_client_initialization_minimal():
    """Test minimal API client initialization."""
    client = GitHubAPIClient(token="test_token_minimal")
    assert client.token == "test_token_minimal"
    assert client.base_url == "https://api.github.com"
    assert client.max_retries == 3
    assert client.rate_limit_wait is True


def test_api_client_custom_settings():
    """Test API client with custom settings."""
    client = GitHubAPIClient(
        token="test_token",
        api_base_url="https://custom.github.com/api/v3",
        max_retries=5,
        backoff_factor=2.0,
        rate_limit_wait=False,
    )
    assert client.base_url == "https://custom.github.com/api/v3"
    assert client.max_retries == 5
    assert client.backoff_factor == 2.0
    assert client.rate_limit_wait is False
