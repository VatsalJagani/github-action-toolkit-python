# pyright: reportPrivateUsage=false
# pyright: reportUnusedVariable=false
# pyright: reportUnusedParameter=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false

import tempfile
from unittest import mock

import pytest

from github_action_toolkit.git_manager import Repo


@pytest.fixture
def mock_git_repo():
    """Mocks GitPython's Repo object."""
    with mock.patch("github_action_toolkit.git_manager.GitRepo") as git_repo_mock:
        yield git_repo_mock


def test_init_with_url(mock_git_repo):
    repo_url = "https://github.com/test/test.git"
    with Repo(url=repo_url) as repo:
        mock_git_repo.clone_from.assert_called_once_with(repo_url, repo.repo_path)
        assert repo.repo is mock_git_repo.clone_from.return_value


def test_init_with_path(mock_git_repo):
    with tempfile.TemporaryDirectory() as path:
        with Repo(path=path) as repo:
            mock_git_repo.assert_called_once_with(path)
            assert repo.repo is mock_git_repo.return_value


def test_configure_git(mock_git_repo):
    # Create the mock repo instance
    repo_instance = mock_git_repo.return_value

    # Create a specific mock for config_writer
    mock_config_writer = mock.Mock()
    repo_instance.config_writer.return_value = mock_config_writer

    # Just entering the context will call configure_git()
    with Repo(path="."):
        pass

    # Now assert the expected behavior
    mock_config_writer.set_value.assert_any_call("user", "name", mock.ANY)
    mock_config_writer.set_value.assert_any_call("user", "email", mock.ANY)
    mock_config_writer.release.assert_called_once()


def test_get_current_branch(mock_git_repo):
    mock_branch = mock.Mock()
    mock_branch.name = "main"
    mock_git_repo.return_value.active_branch = mock_branch

    with Repo(path=".") as repo:
        assert repo.get_current_branch() == "main"


def test_create_new_branch(mock_git_repo):
    with Repo(path=".") as repo:
        repo.create_new_branch("feature/test")
        repo.repo.git.checkout.assert_called_once_with("-b", "feature/test")


def test_add(mock_git_repo):
    with Repo(path=".") as repo:
        repo.add("file.txt")
        repo.repo.git.add.assert_called_once_with("file.txt")


def test_commit(mock_git_repo):
    with Repo(path=".") as repo:
        repo.commit("Test commit")
        repo.repo.git.commit.assert_called_once_with("-m", "Test commit")


def test_add_all_and_commit(mock_git_repo):
    with Repo(path=".") as repo:
        repo.add_all_and_commit("Test all commit")
        repo.repo.git.add.assert_called_once_with(all=True)
        repo.repo.git.commit.assert_called_once_with("-m", "Test all commit")


def test_push(mock_git_repo):
    mock_git_repo.return_value.active_branch.name = "test-branch"

    with Repo(path=".") as repo:
        repo.push()
        repo.repo.git.push.assert_called_once_with("origin", "test-branch")


def test_pull(mock_git_repo):
    mock_git_repo.return_value.active_branch.name = "test-branch"

    with Repo(path=".") as repo:
        repo.pull()
        repo.repo.git.pull.assert_called_once_with("origin", "test-branch")


def test_context_manager_cleanup_true_happy_path(mock_git_repo):
    """When cleanup=True we should fetch, checkout, reset, clean, pull on enter and exit."""
    mock_repo = mock_git_repo.return_value
    mock_repo.active_branch.name = "main"
    # Simulate origin refs containing origin/main
    mock_ref = mock.Mock()
    mock_ref.name = "origin/main"
    mock_repo.remotes.origin.refs = [mock_ref]

    with Repo(path=".", cleanup=True):
        pass

    # Expect two sync cycles (enter and exit)
    assert mock_repo.git.fetch.call_count == 2
    # Checkout to base twice; with remote available we use `checkout -B base origin/base`
    checkout_b_calls = [
        c for c in mock_repo.git.checkout.call_args_list if c.args == ("-B", "main", "origin/main")
    ]
    assert len(checkout_b_calls) == 2
    # Reset to remote ref twice
    reset_remote_calls = [
        c for c in mock_repo.git.reset.call_args_list if c.args == ("--hard", "origin/main")
    ]
    assert len(reset_remote_calls) == 2
    # Clean four times (pre and post, for enter and exit)
    clean_calls = [c for c in mock_repo.git.clean.call_args_list if c.args == ("-fdx",)]
    assert len(clean_calls) == 4
    # Pull twice
    pull_calls = [c for c in mock_repo.git.pull.call_args_list if c.args == ("origin", "main")]
    assert len(pull_calls) == 2


def test_context_manager_cleanup_true_missing_remote_ref(mock_git_repo):
    """If remote ref missing it should fall back to local hard reset only (on enter and exit)."""
    mock_repo = mock_git_repo.return_value
    mock_repo.active_branch.name = "develop"
    # No origin/develop in refs
    mock_repo.remotes.origin.refs = []

    with Repo(path=".", cleanup=True):
        pass

    # Expect two sync cycles (enter and exit)
    assert mock_repo.git.fetch.call_count == 2
    checkout_calls = [c for c in mock_repo.git.checkout.call_args_list if c.args == ("develop",)]
    assert len(checkout_calls) == 2
    # Expect four local hard resets (pre and post, for enter and exit)
    local_hard_resets = [c for c in mock_repo.git.reset.call_args_list if c.args == ("--hard",)]
    assert len(local_hard_resets) == 4
    # Clean four times
    clean_calls = [c for c in mock_repo.git.clean.call_args_list if c.args == ("-fdx",)]
    assert len(clean_calls) == 4
    pull_calls = [c for c in mock_repo.git.pull.call_args_list if c.args == ("origin", "develop")]
    assert len(pull_calls) == 2


def test_context_manager_no_cleanup(mock_git_repo):
    """When cleanup=False none of the destructive git ops should run."""
    mock_repo = mock_git_repo.return_value
    mock_repo.active_branch.name = "main"

    with Repo(path=".", cleanup=False):
        pass

    # Ensure no cleanup-related operations were invoked
    assert not mock_repo.git.fetch.called
    assert not mock_repo.git.clean.called
    assert not mock_repo.git.reset.called
    # checkout only happens for create_new_branch or inside cleanup logic
    # so we verify it's not called here.
    assert not mock_repo.git.checkout.called


@mock.patch("github_action_toolkit.git_manager.Github")
def test_create_pr(mock_github, mock_git_repo):
    mock_repo_instance = mock_git_repo.return_value
    mock_repo_instance.remotes.origin.url = "https://github.com/test/repo.git"

    mock_repo_obj = mock.Mock()
    mock_pr = mock.Mock()
    mock_pr.html_url = "https://github.com/test/repo/pull/1"
    mock_repo_obj.create_pull.return_value = mock_pr

    mock_github.return_value.get_repo.return_value = mock_repo_obj

    with Repo(path=".") as repo:
        pr_url = repo.create_pr(
            github_token="fake-token",
            title="Test PR",
            body="PR Body",
            head="feature/test",
            base="main",
        )

    mock_github.assert_called_once_with("fake-token")
    mock_github.return_value.get_repo.assert_called_once_with("test/repo")
    mock_repo_obj.create_pull.assert_called_once_with(
        title="Test PR", body="PR Body", head="feature/test", base="main"
    )
    assert pr_url == "https://github.com/test/repo/pull/1"
