"""
Test that all imports work as expected after refactoring.

This ensures users can import from the expected locations.
"""


def test_event_models_imports():
    """Test that event models can be imported from github_action_toolkit.event_models."""
    from github_action_toolkit.event_models import (
        Actor,
        BaseEvent,
        Comment,
        Commit,
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
        EnvironmentVariableError,
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
    assert EnvironmentVariableError is not None
    assert GitHubActionError is not None
    assert GitHubAPIError is not None
    assert GitOperationError is not None
    assert InputError is not None
    assert RateLimitError is not None


def test_main_package_imports():
    """Test that main package exports the expected items."""
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

    # Check that the __all__ does not include the functions
    assert "event_payload" not in gat.__all__
    assert "get_event_name" not in gat.__all__
    assert "get_typed_event" not in gat.__all__
    assert "is_pr" not in gat.__all__
    assert "get_pr_number" not in gat.__all__
    assert "head_ref" not in gat.__all__
    assert "base_ref" not in gat.__all__
    assert "get_changed_files" not in gat.__all__
    assert "get_labels" not in gat.__all__
    assert "print_directory_tree" not in gat.__all__
    assert "register_cancellation_handler" not in gat.__all__
    assert "enable_cancellation_support" not in gat.__all__
    assert "disable_cancellation_support" not in gat.__all__
    assert "is_cancellation_enabled" not in gat.__all__

    # Verify that the module objects themselves are not callables
    # (they're modules, not functions)
    if hasattr(gat, "event_payload"):
        assert not callable(gat.event_payload) or str(type(gat.event_payload)) == "<class 'module'>"


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
