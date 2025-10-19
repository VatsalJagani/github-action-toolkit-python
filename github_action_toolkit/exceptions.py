"""
Custom exception taxonomy for github-action-toolkit.

Provides specific exception classes for better error handling and debugging.
"""

from __future__ import annotations


class GitHubActionError(Exception):
    """Base exception for all github-action-toolkit errors."""


class EnvironmentVariableError(GitHubActionError):
    """
    Raised when required environment variables are missing or invalid.

    This typically occurs when the toolkit is not running in a GitHub Actions
    context or required environment variables are not set.
    """


class InputError(GitHubActionError):
    """
    Raised when user input is invalid or cannot be parsed.

    This occurs when converting input values to specific types fails or when
    required inputs are missing.
    """


class GitOperationError(GitHubActionError):
    """
    Raised when git operations fail.

    This occurs during repository operations like clone, checkout, commit, push, etc.
    """


class GitHubAPIError(GitHubActionError):
    """
    Raised when GitHub API operations fail.

    This occurs when interacting with GitHub APIs for artifacts, PRs, etc.
    """


class ConfigurationError(GitHubActionError):
    """
    Raised when configuration is invalid or incomplete.

    This occurs when required configuration parameters are missing or invalid.
    """


class CacheNotFoundError(GitHubActionError):
    """Raised when a cache entry is not found."""


class CacheRestoreError(GitHubActionError):
    """Raised when cache restoration fails."""


class CacheSaveError(GitHubActionError):
    """Raised when cache save fails."""


class CancellationRequested(GitHubActionError):
    """
    Raised when a cancellation signal (SIGTERM, SIGINT) is received.

    This allows code to handle cancellation gracefully by catching this exception.
    """


class RateLimitError(GitHubActionError):
    """Raised when GitHub API rate limit is exceeded."""

    def __init__(self, reset_time: int | None = None):
        self.reset_time: int | None = reset_time
        super().__init__("GitHub API rate limit exceeded")


class APIError(GitHubActionError):
    """Raised when GitHub API returns an error."""

    def __init__(self, status_code: int, message: str):
        self.status_code: int = status_code
        super().__init__(f"GitHub API error ({status_code}): {message}")
