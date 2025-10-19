from __future__ import annotations

import json
import os
from typing import Any

from .event_models import (
    IssueCommentEvent,
    PullRequestEvent,
    PushEvent,
    WorkflowRunEvent,
)


class EventPayload:
    """
    GitHub Actions event payload helper for accessing workflow event data.

    Provides convenient methods to parse and query event data based on the event type.
    """

    def __init__(self) -> None:
        self._payload_cache: dict[str, Any] | None = None

    def clear_cache(self) -> None:
        """Clear the internal payload cache."""
        self._payload_cache = None

    def get_payload(self) -> dict[str, Any]:
        """
        Get GitHub event payload data.

        :returns: dictionary of event payload
        """
        if self._payload_cache is None:
            with open(os.environ["GITHUB_EVENT_PATH"]) as f:
                data: dict[str, Any] = json.load(f)
                self._payload_cache = data
        return self._payload_cache

    def get_event_name(self) -> str:
        """
        Get the name of the event that triggered the workflow.

        :returns: event name (e.g., 'push', 'pull_request', 'issue_comment')
        """
        return os.environ.get("GITHUB_EVENT_NAME", "")

    def get_typed_event(
        self,
    ) -> PushEvent | PullRequestEvent | IssueCommentEvent | WorkflowRunEvent | None:
        """
        Parse the event payload into a strongly typed event model based on the event name.

        :returns: typed event model or None if event type is not supported
        """
        event_name = self.get_event_name()
        payload = self.get_payload()

        event_map = {
            "push": PushEvent,
            "pull_request": PullRequestEvent,
            "pull_request_target": PullRequestEvent,
            "issue_comment": IssueCommentEvent,
            "workflow_run": WorkflowRunEvent,
        }

        event_class = event_map.get(event_name)
        if event_class:
            return event_class.model_validate(payload)
        return None

    def is_pr(self) -> bool:
        """
        Check if the current event is a pull request event.

        :returns: True if the event is a pull request event, False otherwise
        """
        event_name = self.get_event_name()
        return event_name in ("pull_request", "pull_request_target")

    def get_pr_number(self) -> int | None:
        """
        Get the pull request number if the event is a pull request event.

        :returns: PR number or None if not a PR event
        """
        if not self.is_pr():
            return None

        payload = self.get_payload()
        pr_data = payload.get("pull_request")
        if pr_data:
            return pr_data.get("number")
        return None

    def head_ref(self) -> str | None:
        """
        Get the head reference for the event.

        For push events, returns the ref being pushed to.
        For pull request events, returns the head branch.

        :returns: head reference or None
        """
        event_name = self.get_event_name()
        payload = self.get_payload()

        if event_name == "push":
            return payload.get("ref")
        elif event_name in ("pull_request", "pull_request_target"):
            pr_data = payload.get("pull_request", {})
            head_data = pr_data.get("head", {})
            return head_data.get("ref")

        return None

    def base_ref(self) -> str | None:
        """
        Get the base reference for the event.

        For pull request events, returns the base branch.

        :returns: base reference or None
        """
        if not self.is_pr():
            return None

        payload = self.get_payload()
        pr_data = payload.get("pull_request", {})
        base_data = pr_data.get("base", {})
        return base_data.get("ref")

    def get_changed_files(self) -> list[str]:
        """
        Get the list of changed files for the event.

        For push events, returns files added, removed, or modified in commits.

        :returns: list of changed file paths
        """
        event_name = self.get_event_name()
        payload = self.get_payload()

        changed_files: set[str] = set()

        if event_name == "push":
            commits = payload.get("commits", [])
            for commit in commits:
                changed_files.update(commit.get("added", []))
                changed_files.update(commit.get("removed", []))
                changed_files.update(commit.get("modified", []))

        return sorted(changed_files)

    def get_labels(self) -> list[str]:
        """
        Get the list of labels for the event.

        For pull request and issue events, returns the labels.

        :returns: list of label names
        """
        payload = self.get_payload()

        # Try pull_request first
        pr_data = payload.get("pull_request")
        if pr_data:
            labels = pr_data.get("labels", [])
            return [label.get("name", "") for label in labels]

        # Try issue
        issue_data = payload.get("issue")
        if issue_data:
            labels = issue_data.get("labels", [])
            return [label.get("name", "") for label in labels]

        return []
