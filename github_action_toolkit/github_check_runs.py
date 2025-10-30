from __future__ import annotations

import os
from typing import Any

import requests

from . import print_messages as gat

__all__ = ("GitHubCheckRun",)


class GitHubCheckRun:
    """
    GitHub Check Runs API integration for quality gates.

    Creates check runs that appear in the PR interface and can block merges
    based on custom quality criteria. Check runs provide inline feedback and
    can be used to implement quality gates for custom validations.

    Usage:
    ```python
    from github_action_toolkit import GitHubCheckRun

    # Initialize with repository details
    check_run = GitHubCheckRun(
        repo_owner="owner",
        repo_name="repo",
        sha="commit_sha",
        github_token="ghp_..."
    )

    # Create a check run
    result = check_run.create_check_run(
        name="Code Quality",
        status="completed",
        conclusion="success",
        title="All checks passed",
        summary="Quality gates passed successfully"
    )
    ```
    """

    API_BASE = "https://api.github.com"

    def __init__(
        self,
        repo_owner: str,
        repo_name: str,
        sha: str,
        github_token: str | None = None,
    ) -> None:
        """
        Initialize GitHub Check Run.

        :param repo_owner: GitHub repository owner
        :param repo_name: GitHub repository name
        :param sha: Git commit SHA
        :param github_token: GitHub token for API authentication
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.sha = sha

        self.github_token = github_token or os.environ.get("GITHUB_TOKEN")
        if not self.github_token:
            gat.warning("No GitHub token provided - Check Runs will not be created")

        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def create_check_run(
        self,
        name: str,
        status: str = "in_progress",
        conclusion: str | None = None,
        title: str | None = None,
        summary: str | None = None,
        text: str | None = None,
        annotations: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any] | None:
        """
        Create or update a GitHub Check Run.

        :param name: Name of the check run
        :param status: Status (queued, in_progress, completed)
        :param conclusion: Conclusion when completed (success, failure, neutral, cancelled, skipped, timed_out, action_required)
        :param title: Title of the check run
        :param summary: Summary text
        :param text: Detailed text
        :param annotations: List of code annotations
        :returns: Check run response or None if failed
        """
        if not self.github_token:
            gat.warning("Cannot create Check Run without GitHub token")
            return None

        url = f"{self.API_BASE}/repos/{self.repo_owner}/{self.repo_name}/check-runs"

        data: dict[str, Any] = {
            "name": name,
            "head_sha": self.sha,
            "status": status,
        }

        if conclusion and status == "completed":
            data["conclusion"] = conclusion

        if title or summary or text:
            output: dict[str, Any] = {}
            if title:
                output["title"] = title
            if summary:
                output["summary"] = summary
            if text:
                output["text"] = text
            if annotations:
                output["annotations"] = annotations[:50]
            data["output"] = output

        try:
            response = requests.post(url, json=data, headers=self.headers, timeout=30)
            if response.status_code not in [200, 201]:
                gat.error(
                    f"Failed to create Check Run: {response.status_code} - {response.text}"
                )
                return None

            result = response.json()
            if isinstance(result, dict):
                return result
            return None

        except Exception as e:
            gat.error(f"Error creating Check Run: {e}")
            return None
