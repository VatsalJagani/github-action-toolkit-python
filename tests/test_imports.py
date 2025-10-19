"""
Test that all imports work as expected after refactoring.

This ensures users can import from the expected locations.
"""


def test_event_models_imports():
    """Test that event models can be imported from github_action_toolkit.event_models."""
    from github_action_toolkit.event_models import (
        Actor,
        BaseEvent,
        Commit,
        Comment,
        Issue,
        IssueCommentEvent,
        Label,
        PullRequest,
        PullRequestEvent,
        PushEvent,
        Repository,
        WorkflowRun,
        WorkflowRunEvent,
    )

    assert Actor is not None
    assert BaseEvent is not None
    assert Commit is not None
    assert Comment is not None
    assert Issue is not None
    assert IssueCommentEvent is not None
    assert Label is not None
    assert PullRequest is not None
    assert PullRequestEvent is not None
    assert PushEvent is not None
    assert Repository is not None
    assert WorkflowRun is not None
    assert WorkflowRunEvent is not None


def test_exceptions_imports():
    """Test that exceptions can be imported from github_action_toolkit.exceptions."""
    from github_action_toolkit.exceptions import (
        APIError,
        CacheNotFoundError,
        CacheRestoreError,
        CacheSaveError,
        CancellationRequested,
        ConfigurationError,
        EnvironmentError,
        GitHubActionError,
        GitHubAPIError,
        GitOperationError,
        InputError,
        RateLimitError,
    )

    assert APIError is not None
    assert CacheNotFoundError is not None
    assert CacheRestoreError is not None
    assert CacheSaveError is not None
    assert CancellationRequested is not None
    assert ConfigurationError is not None
    assert EnvironmentError is not None
    assert GitHubActionError is not None
    assert GitHubAPIError is not None
    assert GitOperationError is not None
    assert InputError is not None
    assert RateLimitError is not None


def test_main_package_imports():
    """Test that main package still exports the expected items."""
    import github_action_toolkit as gat

    # Classes
    assert hasattr(gat, "JobSummary")
    assert hasattr(gat, "JobSummaryTemplate")
    assert hasattr(gat, "EventPayload")
    assert hasattr(gat, "Debugging")
    assert hasattr(gat, "CancellationHandler")
    assert hasattr(gat, "Repo")
    assert hasattr(gat, "GitRepo")
    assert hasattr(gat, "GitHubCache")
    assert hasattr(gat, "GitHubArtifacts")
    assert hasattr(gat, "GitHubAPIClient")

    # Functions (backward compatibility)
    assert hasattr(gat, "event_payload")
    assert hasattr(gat, "get_event_name")
    assert hasattr(gat, "get_typed_event")
    assert hasattr(gat, "is_pr")
    assert hasattr(gat, "get_pr_number")
    assert hasattr(gat, "head_ref")
    assert hasattr(gat, "base_ref")
    assert hasattr(gat, "get_changed_files")
    assert hasattr(gat, "get_labels")

    assert hasattr(gat, "print_directory_tree")

    assert hasattr(gat, "register_cancellation_handler")
    assert hasattr(gat, "enable_cancellation_support")
    assert hasattr(gat, "disable_cancellation_support")
    assert hasattr(gat, "is_cancellation_enabled")


def test_class_functionality():
    """Test that the new classes work correctly."""
    from github_action_toolkit import CancellationHandler, Debugging, EventPayload

    # Test CancellationHandler can be instantiated
    handler = CancellationHandler()
    assert handler is not None
    assert not handler.is_enabled()

    # Test EventPayload can be instantiated (we can't fully test it without env vars)
    # But we can check the class exists
    assert EventPayload is not None

    # Test Debugging has the expected methods
    assert hasattr(Debugging, "print_directory_tree")


def test_repo_alias():
    """Test that GitRepo is an alias for Repo."""
    from github_action_toolkit import GitRepo, Repo

    assert GitRepo is Repo


def test_exception_hierarchy():
    """Test that exceptions are properly subclassed."""
    from github_action_toolkit.exceptions import (
        APIError,
        CacheNotFoundError,
        CacheRestoreError,
        CacheSaveError,
        CancellationRequested,
        GitHubActionError,
        RateLimitError,
    )

    # Test that all custom exceptions inherit from GitHubActionError
    assert issubclass(CacheNotFoundError, GitHubActionError)
    assert issubclass(CacheRestoreError, GitHubActionError)
    assert issubclass(CacheSaveError, GitHubActionError)
    assert issubclass(CancellationRequested, GitHubActionError)
    assert issubclass(APIError, GitHubActionError)
    assert issubclass(RateLimitError, GitHubActionError)
