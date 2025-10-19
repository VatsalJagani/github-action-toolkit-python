# pyright: reportPrivateUsage=false
# pyright: reportUnusedVariable=false
# pyright: reportUnusedParameter=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false

import tempfile
from pathlib import Path
from unittest import mock

import pytest

from github_action_toolkit.git_manager import Repo


@pytest.fixture
def mock_git_repo():
    """Mocks GitPython's Repo object."""
    with mock.patch("github_action_toolkit.git_manager.GitPythonRepo") as git_repo_mock:
        yield git_repo_mock


def test_init_with_url(mock_git_repo):
    repo_url = "https://github.com/test/test.git"
    with Repo(url=repo_url) as repo:
        mock_git_repo.clone_from.assert_called_once_with(repo_url, repo.repo_path)
        assert repo.repo is mock_git_repo.clone_from.return_value


def test_init_with_path(mock_git_repo):
    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
            mock_git_repo.assert_called_once_with(tmpdir)
            assert repo.repo is mock_git_repo.return_value


def test_configure_git(mock_git_repo):
    # Create the mock repo instance
    repo_instance = mock_git_repo.return_value

    # Create a specific mock for config_writer
    mock_config_writer = mock.Mock()
    repo_instance.config_writer.return_value = mock_config_writer

    with tempfile.TemporaryDirectory() as tmpdir:
        # Just entering the context will call configure_git()
        with Repo(path=tmpdir):
            pass

    # Now assert the expected behavior
    mock_config_writer.set_value.assert_any_call("user", "name", mock.ANY)
    mock_config_writer.set_value.assert_any_call("user", "email", mock.ANY)
    mock_config_writer.release.assert_called_once()


def test_get_current_branch(mock_git_repo):
    mock_branch = mock.Mock()
    mock_branch.name = "main"
    mock_git_repo.return_value.active_branch = mock_branch

    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
            assert repo.get_current_branch() == "main"


def test_create_new_branch(mock_git_repo):
    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
            repo.create_new_branch("feature/test")
            repo.repo.git.checkout.assert_called_once_with("-b", "feature/test")


def test_add(mock_git_repo):
    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
            repo.add("file.txt")
            repo.repo.git.add.assert_called_once_with("file.txt")


def test_commit(mock_git_repo):
    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
            repo.commit("Test commit")
            repo.repo.git.commit.assert_called_once_with("-m", "Test commit")


def test_add_all_and_commit(mock_git_repo):
    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
            repo.add_all_and_commit("Test all commit")
            repo.repo.git.add.assert_called_once_with(all=True)
            repo.repo.git.commit.assert_called_once_with("-m", "Test all commit")


def test_push(mock_git_repo):
    mock_git_repo.return_value.active_branch.name = "test-branch"

    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
            repo.push()
            repo.repo.git.push.assert_called_once_with("origin", "test-branch")


def test_pull(mock_git_repo):
    mock_git_repo.return_value.active_branch.name = "test-branch"

    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
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

    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir, cleanup=True):
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

    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir, cleanup=True):
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

    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir, cleanup=False):
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

    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
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


def test_shallow_clone(mock_git_repo):
    repo_url = "https://github.com/test/test.git"
    with Repo(url=repo_url, depth=1) as repo:
        mock_git_repo.clone_from.assert_called_once_with(repo_url, repo.repo_path, depth=1)


def test_single_branch_clone(mock_git_repo):
    repo_url = "https://github.com/test/test.git"
    with Repo(url=repo_url, single_branch=True) as repo:
        mock_git_repo.clone_from.assert_called_once_with(
            repo_url, repo.repo_path, single_branch=True
        )


def test_shallow_single_branch_clone(mock_git_repo):
    repo_url = "https://github.com/test/test.git"
    with Repo(url=repo_url, depth=1, single_branch=True) as repo:
        mock_git_repo.clone_from.assert_called_once_with(
            repo_url, repo.repo_path, depth=1, single_branch=True
        )


@mock.patch("github_action_toolkit.git_manager.subprocess.run")
def test_configure_safe_directory(mock_run, mock_git_repo):
    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
            repo.configure_safe_directory()

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == [
            "git",
            "config",
            "--global",
            "--add",
            "safe.directory",
            tmpdir,
        ]


def test_sparse_checkout_init(mock_git_repo):
    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
            repo.sparse_checkout_init()
            repo.repo.git.config.assert_any_call("core.sparseCheckout", "true")
            repo.repo.git.config.assert_any_call("core.sparseCheckoutCone", "true")


def test_sparse_checkout_init_no_cone(mock_git_repo):
    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
            repo.sparse_checkout_init(cone_mode=False)
            repo.repo.git.config.assert_called_once_with("core.sparseCheckout", "true")


def test_submodule_init(mock_git_repo):
    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
            repo.submodule_init()
            repo.repo.git.submodule.assert_called_once_with("init")


def test_submodule_update(mock_git_repo):
    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
            repo.submodule_update()
            repo.repo.git.submodule.assert_called_once_with("update")


def test_submodule_update_recursive(mock_git_repo):
    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
            repo.submodule_update(recursive=True)
            repo.repo.git.submodule.assert_called_once_with("update", "--recursive")


def test_submodule_update_remote(mock_git_repo):
    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
            repo.submodule_update(remote=True)
            repo.repo.git.submodule.assert_called_once_with("update", "--remote")


def test_submodule_update_recursive_remote(mock_git_repo):
    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
            repo.submodule_update(recursive=True, remote=True)
            repo.repo.git.submodule.assert_called_once_with("update", "--recursive", "--remote")


def test_configure_gpg_signing(mock_git_repo):
    mock_config_writer = mock.Mock()
    mock_git_repo.return_value.config_writer.return_value = mock_config_writer

    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
            repo.configure_gpg_signing(key_id="ABC123", program="/usr/bin/gpg")

    mock_config_writer.set_value.assert_any_call("commit", "gpgsign", "true")
    mock_config_writer.set_value.assert_any_call("user", "signingkey", "ABC123")
    mock_config_writer.set_value.assert_any_call("gpg", "program", "/usr/bin/gpg")
    mock_config_writer.release.assert_called()


def test_configure_ssh_signing(mock_git_repo):
    mock_config_writer = mock.Mock()
    mock_git_repo.return_value.config_writer.return_value = mock_config_writer

    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
            repo.configure_ssh_signing(key_path="/home/user/.ssh/id_ed25519.pub")

    mock_config_writer.set_value.assert_any_call("gpg", "format", "ssh")
    mock_config_writer.set_value.assert_any_call("commit", "gpgsign", "true")
    mock_config_writer.set_value.assert_any_call(
        "user", "signingkey", "/home/user/.ssh/id_ed25519.pub"
    )
    mock_config_writer.release.assert_called()


def test_set_remote_url(mock_git_repo):
    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
            repo.set_remote_url("origin", "https://github.com/test/repo.git")
            repo.repo.git.remote.assert_called_once_with(
                "set-url", "origin", "https://github.com/test/repo.git"
            )


def test_set_remote_url_with_token(mock_git_repo):
    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
            repo.set_remote_url("origin", "https://github.com/test/repo.git", token="ghp_token123")
            repo.repo.git.remote.assert_called_once_with(
                "set-url",
                "origin",
                "https://x-access-token:ghp_token123@github.com/test/repo.git",
            )


def test_create_tag(mock_git_repo):
    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
            repo.create_tag("v1.0.0", message="Release 1.0.0")
            repo.repo.git.tag.assert_called_once_with("-a", "v1.0.0", "-m", "Release 1.0.0")


def test_create_tag_signed(mock_git_repo):
    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
            repo.create_tag("v1.0.0", message="Release 1.0.0", signed=True)
            repo.repo.git.tag.assert_called_once_with("-s", "v1.0.0", "-m", "Release 1.0.0")


def test_create_tag_lightweight(mock_git_repo):
    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
            repo.create_tag("v1.0.0")
            repo.repo.git.tag.assert_called_once_with("v1.0.0")


def test_list_tags(mock_git_repo):
    mock_git_repo.return_value.git.tag.return_value = "v1.0.0\nv1.1.0\nv2.0.0"

    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
            tags = repo.list_tags()
            assert tags == ["v1.0.0", "v1.1.0", "v2.0.0"]
            repo.repo.git.tag.assert_called_once_with("-l")


def test_list_tags_with_pattern(mock_git_repo):
    mock_git_repo.return_value.git.tag.return_value = "v1.0.0\nv1.1.0"

    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
            tags = repo.list_tags(pattern="v1.*")
            assert tags == ["v1.0.0", "v1.1.0"]
            repo.repo.git.tag.assert_called_once_with("-l", "v1.*")


def test_push_tag(mock_git_repo):
    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
            repo.push_tag("v1.0.0")
            repo.repo.git.push.assert_called_once_with("origin", "v1.0.0")


def test_push_all_tags(mock_git_repo):
    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
            repo.push_all_tags()
            repo.repo.git.push.assert_called_once_with("origin", "--tags")


def test_delete_tag(mock_git_repo):
    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
            repo.delete_tag("v1.0.0")
            repo.repo.git.tag.assert_called_once_with("-d", "v1.0.0")


def test_delete_tag_with_remote(mock_git_repo):
    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
            repo.delete_tag("v1.0.0", remote=True)
            repo.repo.git.tag.assert_called_once_with("-d", "v1.0.0")
            repo.repo.git.push.assert_called_once_with("origin", "--delete", "v1.0.0")


def test_get_latest_tag(mock_git_repo):
    mock_git_repo.return_value.git.describe.return_value = "v2.0.0"

    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
            latest = repo.get_latest_tag()
            assert latest == "v2.0.0"
            repo.repo.git.describe.assert_called_once_with("--tags", "--abbrev=0")


def test_get_latest_tag_no_tags(mock_git_repo):
    mock_git_repo.return_value.git.describe.side_effect = Exception("No tags")

    with tempfile.TemporaryDirectory() as tmpdir:
        with Repo(path=tmpdir) as repo:
            latest = repo.get_latest_tag()
            assert latest is None


def test_extract_changelog_section():
    changelog_content = """# Changelog

## Unreleased

- New feature A
- Bug fix B

## v1.0.0 - 2024-01-01

- Initial release

## v0.9.0 - 2023-12-01

- Beta release
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        changelog_path = Path(tmpdir) / "CHANGELOG.md"
        changelog_path.write_text(changelog_content)

        with mock.patch("github_action_toolkit.git_manager.GitPythonRepo"):
            with Repo(path=tmpdir) as repo:
                # Extract Unreleased
                section = repo.extract_changelog_section()
                assert "New feature A" in section
                assert "Bug fix B" in section
                assert "Initial release" not in section

                # Extract specific version
                section = repo.extract_changelog_section(version="v1.0.0")
                assert "Initial release" in section
                assert "New feature A" not in section


def test_prepare_release():
    changelog_content = """# Changelog

## Unreleased

- Feature for v2.0.0

## v1.0.0 - 2024-01-01

- Initial release
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        changelog_path = Path(tmpdir) / "CHANGELOG.md"
        changelog_path.write_text(changelog_content)

        with mock.patch("github_action_toolkit.git_manager.GitPythonRepo"):
            with Repo(path=tmpdir) as repo:
                result = repo.prepare_release("v2.0.0")

                assert result["version"] == "v2.0.0"
                assert "Feature for v2.0.0" in result["changelog"]
                assert "tag" in result
                repo.repo.git.tag.assert_called_once()


def test_prepare_release_no_tag():
    with tempfile.TemporaryDirectory() as tmpdir:
        changelog_path = Path(tmpdir) / "CHANGELOG.md"
        changelog_path.write_text("# Changelog\n\n## Unreleased\n\n- New feature")

        with mock.patch("github_action_toolkit.git_manager.GitPythonRepo"):
            with Repo(path=tmpdir) as repo:
                result = repo.prepare_release("v1.0.0", create_tag_flag=False)

                assert result["version"] == "v1.0.0"
                assert "tag" not in result
                repo.repo.git.tag.assert_not_called()
