# pyright: reportPrivateUsage=false
# pyright: reportUnusedVariable=false
# pyright: reportUnusedParameter=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUnknownMemberType=false

import json
import os
from typing import Any
from unittest import mock

import github_action_toolkit as gat
from github_action_toolkit.event_models import PullRequestEvent, PushEvent


def test_event_payload(tmpdir: Any) -> None:
    file = tmpdir.join("summary")
    payload = {"test": "test"}
    file.write(json.dumps(payload))

    with mock.patch.dict(os.environ, {"GITHUB_EVENT_PATH": file.strpath}):
        event = gat.EventPayload()
        data = event.get_payload()

    assert data == payload


def test_get_event_name() -> None:
    with mock.patch.dict(os.environ, {"GITHUB_EVENT_NAME": "push"}):
        event = gat.EventPayload()
        assert event.get_event_name() == "push"

    with mock.patch.dict(os.environ, {"GITHUB_EVENT_NAME": "pull_request"}):
        event = gat.EventPayload()
        assert event.get_event_name() == "pull_request"


def test_is_pr() -> None:
    with mock.patch.dict(os.environ, {"GITHUB_EVENT_NAME": "pull_request"}):
        event = gat.EventPayload()
        assert event.is_pr() is True

    with mock.patch.dict(os.environ, {"GITHUB_EVENT_NAME": "pull_request_target"}):
        event = gat.EventPayload()
        assert event.is_pr() is True

    with mock.patch.dict(os.environ, {"GITHUB_EVENT_NAME": "push"}):
        event = gat.EventPayload()
        assert event.is_pr() is False


def test_get_pr_number(tmpdir: Any) -> None:
    file = tmpdir.join("event")
    payload = {
        "pull_request": {"number": 123},
        "repository": {
            "id": 1,
            "node_id": "R_1",
            "name": "test",
            "full_name": "owner/test",
            "private": False,
            "owner": {
                "login": "owner",
                "id": 1,
                "node_id": "U_1",
                "avatar_url": "https://example.com",
                "gravatar_id": "",
                "url": "https://example.com",
                "html_url": "https://example.com",
                "type": "User",
            },
            "html_url": "https://example.com",
            "fork": False,
            "url": "https://example.com",
            "default_branch": "main",
        },
        "sender": {
            "login": "user",
            "id": 2,
            "node_id": "U_2",
            "avatar_url": "https://example.com",
            "gravatar_id": "",
            "url": "https://example.com",
            "html_url": "https://example.com",
            "type": "User",
        },
    }
    file.write(json.dumps(payload))

    with mock.patch.dict(
        os.environ, {"GITHUB_EVENT_PATH": file.strpath, "GITHUB_EVENT_NAME": "pull_request"}
    ):
        # Clear cache
        event = gat.EventPayload()
        event.clear_cache()
        event = gat.EventPayload()
        assert event.get_pr_number() == 123

    with mock.patch.dict(
        os.environ, {"GITHUB_EVENT_PATH": file.strpath, "GITHUB_EVENT_NAME": "push"}
    ):
        event = gat.EventPayload()
        event.clear_cache()
        event = gat.EventPayload()
        assert event.get_pr_number() is None


def test_head_ref(tmpdir: Any) -> None:
    # Test push event
    push_file = tmpdir.join("push_event")
    push_payload = {
        "ref": "refs/heads/feature-branch",
        "repository": {
            "id": 1,
            "node_id": "R_1",
            "name": "test",
            "full_name": "owner/test",
            "private": False,
            "owner": {
                "login": "owner",
                "id": 1,
                "node_id": "U_1",
                "avatar_url": "https://example.com",
                "gravatar_id": "",
                "url": "https://example.com",
                "html_url": "https://example.com",
                "type": "User",
            },
            "html_url": "https://example.com",
            "fork": False,
            "url": "https://example.com",
            "default_branch": "main",
        },
        "sender": {
            "login": "user",
            "id": 2,
            "node_id": "U_2",
            "avatar_url": "https://example.com",
            "gravatar_id": "",
            "url": "https://example.com",
            "html_url": "https://example.com",
            "type": "User",
        },
    }
    push_file.write(json.dumps(push_payload))

    with mock.patch.dict(
        os.environ, {"GITHUB_EVENT_PATH": push_file.strpath, "GITHUB_EVENT_NAME": "push"}
    ):
        event = gat.EventPayload()
        event.clear_cache()
        event = gat.EventPayload()
        assert event.head_ref() == "refs/heads/feature-branch"

    # Test pull_request event
    pr_file = tmpdir.join("pr_event")
    pr_payload = {
        "pull_request": {
            "head": {"ref": "feature-branch"},
            "base": {"ref": "main"},
        },
        "repository": {
            "id": 1,
            "node_id": "R_1",
            "name": "test",
            "full_name": "owner/test",
            "private": False,
            "owner": {
                "login": "owner",
                "id": 1,
                "node_id": "U_1",
                "avatar_url": "https://example.com",
                "gravatar_id": "",
                "url": "https://example.com",
                "html_url": "https://example.com",
                "type": "User",
            },
            "html_url": "https://example.com",
            "fork": False,
            "url": "https://example.com",
            "default_branch": "main",
        },
        "sender": {
            "login": "user",
            "id": 2,
            "node_id": "U_2",
            "avatar_url": "https://example.com",
            "gravatar_id": "",
            "url": "https://example.com",
            "html_url": "https://example.com",
            "type": "User",
        },
    }
    pr_file.write(json.dumps(pr_payload))

    with mock.patch.dict(
        os.environ, {"GITHUB_EVENT_PATH": pr_file.strpath, "GITHUB_EVENT_NAME": "pull_request"}
    ):
        event = gat.EventPayload()
        event.clear_cache()
        event = gat.EventPayload()
        assert event.head_ref() == "feature-branch"


def test_base_ref(tmpdir: Any) -> None:
    pr_file = tmpdir.join("pr_event")
    pr_payload = {
        "pull_request": {
            "head": {"ref": "feature-branch"},
            "base": {"ref": "main"},
        },
        "repository": {
            "id": 1,
            "node_id": "R_1",
            "name": "test",
            "full_name": "owner/test",
            "private": False,
            "owner": {
                "login": "owner",
                "id": 1,
                "node_id": "U_1",
                "avatar_url": "https://example.com",
                "gravatar_id": "",
                "url": "https://example.com",
                "html_url": "https://example.com",
                "type": "User",
            },
            "html_url": "https://example.com",
            "fork": False,
            "url": "https://example.com",
            "default_branch": "main",
        },
        "sender": {
            "login": "user",
            "id": 2,
            "node_id": "U_2",
            "avatar_url": "https://example.com",
            "gravatar_id": "",
            "url": "https://example.com",
            "html_url": "https://example.com",
            "type": "User",
        },
    }
    pr_file.write(json.dumps(pr_payload))

    with mock.patch.dict(
        os.environ, {"GITHUB_EVENT_PATH": pr_file.strpath, "GITHUB_EVENT_NAME": "pull_request"}
    ):
        event = gat.EventPayload()
        event.clear_cache()
        event = gat.EventPayload()
        assert event.base_ref() == "main"

    with mock.patch.dict(
        os.environ, {"GITHUB_EVENT_PATH": pr_file.strpath, "GITHUB_EVENT_NAME": "push"}
    ):
        event = gat.EventPayload()
        event.clear_cache()
        event = gat.EventPayload()
        assert event.base_ref() is None


def test_get_changed_files(tmpdir: Any) -> None:
    push_file = tmpdir.join("push_event")
    push_payload = {
        "ref": "refs/heads/main",
        "commits": [
            {
                "added": ["file1.py", "file2.py"],
                "removed": ["old.py"],
                "modified": ["existing.py"],
            },
            {"added": ["file3.py"], "removed": [], "modified": ["file1.py"]},
        ],
        "repository": {
            "id": 1,
            "node_id": "R_1",
            "name": "test",
            "full_name": "owner/test",
            "private": False,
            "owner": {
                "login": "owner",
                "id": 1,
                "node_id": "U_1",
                "avatar_url": "https://example.com",
                "gravatar_id": "",
                "url": "https://example.com",
                "html_url": "https://example.com",
                "type": "User",
            },
            "html_url": "https://example.com",
            "fork": False,
            "url": "https://example.com",
            "default_branch": "main",
        },
        "sender": {
            "login": "user",
            "id": 2,
            "node_id": "U_2",
            "avatar_url": "https://example.com",
            "gravatar_id": "",
            "url": "https://example.com",
            "html_url": "https://example.com",
            "type": "User",
        },
    }
    push_file.write(json.dumps(push_payload))

    with mock.patch.dict(
        os.environ, {"GITHUB_EVENT_PATH": push_file.strpath, "GITHUB_EVENT_NAME": "push"}
    ):
        event = gat.EventPayload()
        event.clear_cache()
        event = gat.EventPayload()
        files = event.get_changed_files()
        assert sorted(files) == [
            "existing.py",
            "file1.py",
            "file2.py",
            "file3.py",
            "old.py",
        ]


def test_get_labels(tmpdir: Any) -> None:
    pr_file = tmpdir.join("pr_event")
    pr_payload = {
        "pull_request": {
            "labels": [
                {"name": "bug", "color": "red"},
                {"name": "enhancement", "color": "blue"},
            ]
        },
        "repository": {
            "id": 1,
            "node_id": "R_1",
            "name": "test",
            "full_name": "owner/test",
            "private": False,
            "owner": {
                "login": "owner",
                "id": 1,
                "node_id": "U_1",
                "avatar_url": "https://example.com",
                "gravatar_id": "",
                "url": "https://example.com",
                "html_url": "https://example.com",
                "type": "User",
            },
            "html_url": "https://example.com",
            "fork": False,
            "url": "https://example.com",
            "default_branch": "main",
        },
        "sender": {
            "login": "user",
            "id": 2,
            "node_id": "U_2",
            "avatar_url": "https://example.com",
            "gravatar_id": "",
            "url": "https://example.com",
            "html_url": "https://example.com",
            "type": "User",
        },
    }
    pr_file.write(json.dumps(pr_payload))

    with mock.patch.dict(
        os.environ, {"GITHUB_EVENT_PATH": pr_file.strpath, "GITHUB_EVENT_NAME": "pull_request"}
    ):
        event = gat.EventPayload()
        event.clear_cache()
        event = gat.EventPayload()
        labels = event.get_labels()
        assert labels == ["bug", "enhancement"]


def test_get_typed_event_push(tmpdir: Any) -> None:
    push_file = tmpdir.join("push_event")
    push_payload = {
        "ref": "refs/heads/main",
        "before": "abc123",
        "after": "def456",
        "commits": [],
        "repository": {
            "id": 1,
            "node_id": "R_1",
            "name": "test",
            "full_name": "owner/test",
            "private": False,
            "owner": {
                "login": "owner",
                "id": 1,
                "node_id": "U_1",
                "avatar_url": "https://example.com",
                "gravatar_id": "",
                "url": "https://example.com",
                "html_url": "https://example.com",
                "type": "User",
            },
            "html_url": "https://example.com",
            "fork": False,
            "url": "https://example.com",
            "default_branch": "main",
        },
        "sender": {
            "login": "user",
            "id": 2,
            "node_id": "U_2",
            "avatar_url": "https://example.com",
            "gravatar_id": "",
            "url": "https://example.com",
            "html_url": "https://example.com",
            "type": "User",
        },
    }
    push_file.write(json.dumps(push_payload))

    with mock.patch.dict(
        os.environ, {"GITHUB_EVENT_PATH": push_file.strpath, "GITHUB_EVENT_NAME": "push"}
    ):
        event = gat.EventPayload()
        event.clear_cache()
        event = gat.EventPayload()
        event = event.get_typed_event()
        assert isinstance(event, PushEvent)
        assert event.ref == "refs/heads/main"
        assert event.before == "abc123"
        assert event.after == "def456"


def test_get_typed_event_pull_request(tmpdir: Any) -> None:
    pr_file = tmpdir.join("pr_event")
    pr_payload = {
        "action": "opened",
        "number": 42,
        "pull_request": {
            "id": 1,
            "node_id": "PR_1",
            "number": 42,
            "state": "open",
            "locked": False,
            "title": "Test PR",
            "user": {
                "login": "user",
                "id": 2,
                "node_id": "U_2",
                "avatar_url": "https://example.com",
                "gravatar_id": "",
                "url": "https://example.com",
                "html_url": "https://example.com",
                "type": "User",
            },
            "html_url": "https://example.com/pr/42",
            "diff_url": "https://example.com/pr/42.diff",
            "patch_url": "https://example.com/pr/42.patch",
            "base": {"ref": "main"},
            "head": {"ref": "feature"},
        },
        "repository": {
            "id": 1,
            "node_id": "R_1",
            "name": "test",
            "full_name": "owner/test",
            "private": False,
            "owner": {
                "login": "owner",
                "id": 1,
                "node_id": "U_1",
                "avatar_url": "https://example.com",
                "gravatar_id": "",
                "url": "https://example.com",
                "html_url": "https://example.com",
                "type": "User",
            },
            "html_url": "https://example.com",
            "fork": False,
            "url": "https://example.com",
            "default_branch": "main",
        },
        "sender": {
            "login": "user",
            "id": 2,
            "node_id": "U_2",
            "avatar_url": "https://example.com",
            "gravatar_id": "",
            "url": "https://example.com",
            "html_url": "https://example.com",
            "type": "User",
        },
    }
    pr_file.write(json.dumps(pr_payload))

    with mock.patch.dict(
        os.environ, {"GITHUB_EVENT_PATH": pr_file.strpath, "GITHUB_EVENT_NAME": "pull_request"}
    ):
        event = gat.EventPayload()
        event.clear_cache()
        event = gat.EventPayload()
        event = event.get_typed_event()
        assert isinstance(event, PullRequestEvent)
        assert event.action == "opened"
        assert event.number == 42
        assert event.pull_request.title == "Test PR"


# Property-based tests


from hypothesis import given
from hypothesis import strategies as st


@given(st.sampled_from(["push", "pull_request", "pull_request_target"]))
def test_is_pr_with_various_event_names(event_name: str) -> None:
    """Property test: is_pr correctly identifies PR events."""
    with mock.patch.dict(os.environ, {"GITHUB_EVENT_NAME": event_name}):
        event = gat.EventPayload()
        result = event.is_pr()
        expected = event_name in ["pull_request", "pull_request_target"]
        assert result == expected


@given(
    st.integers(min_value=1, max_value=999999),
    st.text(min_size=1, max_size=50),
)
def test_get_pr_number_with_various_payloads(pr_number: int, repo_name: str) -> None:
    """Property test: get_pr_number extracts PR number from payload."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        payload = {
            "pull_request": {"number": pr_number},
            "repository": {
                "id": 1,
                "node_id": "R_1",
                "name": repo_name,
                "full_name": f"owner/{repo_name}",
                "private": False,
                "owner": {
                    "login": "owner",
                    "id": 1,
                    "node_id": "U_1",
                    "avatar_url": "https://example.com",
                    "gravatar_id": "",
                    "url": "https://example.com",
                    "html_url": "https://example.com",
                    "type": "User",
                },
                "html_url": "https://example.com",
                "fork": False,
                "url": "https://example.com",
                "default_branch": "main",
            },
            "sender": {
                "login": "user",
                "id": 2,
                "node_id": "U_2",
                "avatar_url": "https://example.com",
                "gravatar_id": "",
                "url": "https://example.com",
                "html_url": "https://example.com",
                "type": "User",
            },
        }
        json.dump(payload, f)
        filepath = f.name

    try:
        with mock.patch.dict(
            os.environ, {"GITHUB_EVENT_PATH": filepath, "GITHUB_EVENT_NAME": "pull_request"}
        ):
            event = gat.EventPayload()
            event.clear_cache()
            event = gat.EventPayload()
            result = event.get_pr_number()
            assert result == pr_number
    finally:
        os.unlink(filepath)
