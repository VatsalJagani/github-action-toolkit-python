from __future__ import annotations

import os
import time
from collections.abc import Callable, Iterator
from typing import Any, TypeVar

import requests
from github import Github as PyGithub
from github import GithubException
from github.AuthenticatedUser import AuthenticatedUser
from github.GithubObject import GithubObject
from github.NamedUser import NamedUser
from github.Organization import Organization
from github.PaginatedList import PaginatedList
from github.Repository import Repository
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

__all__ = (
    "GitHubAPIClient",
    "RateLimitError",
    "APIError",
)

T = TypeVar("T", bound=GithubObject)


class RateLimitError(Exception):
    """Raised when GitHub API rate limit is exceeded."""

    def __init__(self, reset_time: int | None = None):
        self.reset_time: int | None = reset_time
        super().__init__("GitHub API rate limit exceeded")


class APIError(Exception):
    """Raised when GitHub API returns an error."""

    def __init__(self, status_code: int, message: str):
        self.status_code: int = status_code
        super().__init__(f"GitHub API error ({status_code}): {message}")


class GitHubAPIClient:
    """
    A typed GitHub API client with rate limit handling, pagination support,
    and base URL override for GitHub Enterprise Server (GHES).

    Wraps PyGithub for REST API access with enhanced features:
    - Automatic rate limit detection and backoff
    - Conditional requests with ETag support
    - Configurable base URL for GHES
    - Built-in retry logic with exponential backoff
    - Typed response handling

    Usage:
    ```python
    from github_action_toolkit import GitHubAPIClient

    # Standard GitHub.com usage
    client = GitHubAPIClient(token="ghp_...")

    # Example with GitHub Enterprise Server
    client = GitHubAPIClient(
        token="ghp_...",
        api_base_url="https://github.mycompany.com/api/v3"
    )

    # Get repository
    repo = client.get_repo("owner/repo")

    # Handle pagination
    for issue in client.paginate(repo.get_issues):
        print(issue.title)
    ```
    """

    def __init__(
        self,
        token: str | None = None,
        api_base_url: str | None = None,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        rate_limit_wait: bool = True,
    ):
        """
        Initialize the GitHub API client.

        :param token: GitHub personal access token (defaults to GITHUB_TOKEN env var)
        :param api_base_url: Base URL for GitHub API (for GHES support)
        :param max_retries: Maximum number of retries for failed requests
        :param backoff_factor: Exponential backoff factor for retries
        :param rate_limit_wait: Whether to automatically wait when rate limited
        """
        self.token: str | None = token or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            msg = "GitHub token is required. Set GITHUB_TOKEN env var or pass token parameter."
            raise ValueError(msg)

        self.base_url: str = api_base_url or "https://api.github.com"
        self.max_retries: int = max_retries
        self.backoff_factor: float = backoff_factor
        self.rate_limit_wait: bool = rate_limit_wait

        # Initialize PyGithub with custom base URL if provided
        self._github: PyGithub
        if api_base_url:
            self._github = PyGithub(login_or_token=self.token, base_url=api_base_url)
        else:
            self._github = PyGithub(login_or_token=self.token)

        # Create requests session with retry logic
        self._session: requests.Session = self._create_session()

        # Cache for conditional requests (ETags)
        self._etag_cache: dict[str, tuple[str, Any]] = {}

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=self.backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    @property
    def github(self) -> PyGithub:
        """Access the underlying PyGithub instance."""
        return self._github

    def get_repository(self, full_name_or_id: str | int) -> Repository:
        """
        Get a repository by full name or ID.

        :param full_name_or_id: Repository full name (owner/repo) or ID
        :returns: Repository object
        """
        return self._with_rate_limit_handling(
            lambda: self._github.get_repo(full_name_or_id=full_name_or_id)
        )

    def get_user(self, login: str | None = None) -> NamedUser | AuthenticatedUser:
        """
        Get a user by login. If login is None, returns the authenticated user.

        :param login: User login (optional)
        :returns: User object
        """
        if login:
            return self._with_rate_limit_handling(lambda: self._github.get_user(login=login))
        return self._with_rate_limit_handling(lambda: self._github.get_user())

    def get_organization(self, login: str) -> Organization:
        """
        Get an organization by login.

        :param login: Organization login
        :returns: Organization object
        """
        return self._with_rate_limit_handling(lambda: self._github.get_organization(login))

    def paginate(
        self,
        paginated_list: PaginatedList[T] | Callable[..., PaginatedList[T]],
        *args: Any,
        **kwargs: Any,
    ) -> Iterator[T]:
        """
        Iterate through a paginated list with automatic rate limit handling.

        :param paginated_list: PaginatedList or callable that returns one
        :param args: Arguments to pass to callable
        :param kwargs: Keyword arguments to pass to callable
        :yields: Items from the paginated list
        """
        if callable(paginated_list):
            paginated_list = paginated_list(*args, **kwargs)

        for item in paginated_list:
            yield self._with_rate_limit_handling(lambda item=item: item)

    def request(
        self,
        method: str,
        url: str,
        use_etag: bool = False,
        **kwargs: Any,
    ) -> requests.Response:
        """
        Make a raw HTTP request to the GitHub API with rate limit handling.

        :param method: HTTP method (GET, POST, etc.)
        :param url: API endpoint URL (relative to base_url or absolute)
        :param use_etag: Whether to use ETag for conditional requests
        :param kwargs: Additional arguments for requests
        :returns: Response object
        """
        if not url.startswith("http"):
            url = f"{self.base_url}/{url.lstrip('/')}"

        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"token {self.token}"
        headers["Accept"] = headers.get("Accept", "application/vnd.github+json")

        # Handle conditional requests with ETag
        if use_etag and url in self._etag_cache:
            cached_etag, cached_response = self._etag_cache[url]
            headers["If-None-Match"] = cached_etag

        response = self._session.request(method, url, headers=headers, **kwargs)

        # Handle rate limiting
        if response.status_code == 403:
            remaining = response.headers.get("X-RateLimit-Remaining", "0")
            if remaining == "0":
                reset_time = int(response.headers.get("X-RateLimit-Reset", "0"))
                if self.rate_limit_wait:
                    self._wait_for_rate_limit(reset_time)
                    # Retry the request after waiting
                    return self.request(method, url, use_etag=use_etag, **kwargs)
                else:
                    raise RateLimitError(reset_time)

        # Handle 304 Not Modified for conditional requests
        if response.status_code == 304 and use_etag:
            _, cached_response = self._etag_cache[url]
            return cached_response

        # Cache ETag for future conditional requests
        if use_etag and "ETag" in response.headers:
            self._etag_cache[url] = (response.headers["ETag"], response)

        # Raise on error status codes
        if response.status_code >= 400:
            error_message = response.text
            try:
                error_data = response.json()
                error_message = error_data.get("message", error_message)
            except Exception:  # noqa: BLE001
                pass
            raise APIError(response.status_code, error_message)

        return response

    def graphql(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Execute a GraphQL query against the GitHub API.

        :param query: GraphQL query string
        :param variables: Variables for the query
        :returns: Query result data
        """
        # Remove /api/v3 suffix if present to build GraphQL URL
        base = self.base_url
        if base.endswith("/api/v3"):
            base = base[:-7]  # Remove '/api/v3'
        url = f"{base}/api/graphql"
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        response = self.request("POST", url, json=payload)
        result = response.json()

        if "errors" in result:
            errors = result["errors"]
            error_messages = [err.get("message", str(err)) for err in errors]
            raise APIError(response.status_code, "; ".join(error_messages))

        return result.get("data", {})

    def get_rate_limit(self) -> dict[str, Any]:
        """
        Get current rate limit status.

        :returns: Dictionary with rate limit information
        """
        rate_limit = self._github.get_rate_limit()
        return {
            "core": {
                "limit": rate_limit.core.limit,  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
                "remaining": rate_limit.core.remaining,  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
                "reset": rate_limit.core.reset.timestamp(),  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
            },
            "search": {
                "limit": rate_limit.search.limit,  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
                "remaining": rate_limit.search.remaining,  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
                "reset": rate_limit.search.reset.timestamp(),  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
            },
            "graphql": {
                "limit": rate_limit.graphql.limit,  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
                "remaining": rate_limit.graphql.remaining,  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
                "reset": rate_limit.graphql.reset.timestamp(),  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
            },
        }

    def _with_rate_limit_handling(self, func: Callable[[], T]) -> T:
        """
        Execute a function with automatic rate limit handling.

        :param func: Function to execute
        :returns: Result of the function
        """
        try:
            return func()
        except GithubException as e:
            if e.status == 403 and "rate limit" in str(e).lower():
                if self.rate_limit_wait:
                    rate_limit = self._github.get_rate_limit()
                    reset_time = int(rate_limit.core.reset.timestamp())  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownArgumentType]
                    self._wait_for_rate_limit(reset_time)
                    # Retry after waiting
                    return func()
                else:
                    raise RateLimitError() from e
            raise APIError(e.status, str(e.data)) from e

    def _wait_for_rate_limit(self, reset_time: int) -> None:
        """
        Wait until the rate limit resets.

        :param reset_time: Unix timestamp when rate limit resets
        """
        wait_time = max(0, reset_time - int(time.time())) + 1
        if wait_time > 0:
            print(f"Rate limit exceeded. Waiting {wait_time} seconds until reset...")
            time.sleep(wait_time)
