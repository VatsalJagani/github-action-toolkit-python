from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Actor(BaseModel):
    """Represents a GitHub user or organization."""

    login: str
    id: int
    node_id: str
    avatar_url: str
    gravatar_id: str = ""
    url: str
    html_url: str
    type: str


class Repository(BaseModel):
    """Represents a GitHub repository."""

    id: int
    node_id: str
    name: str
    full_name: str
    private: bool
    owner: Actor
    html_url: str
    description: str | None = None
    fork: bool
    url: str
    default_branch: str


class Commit(BaseModel):
    """Represents a git commit."""

    id: str
    tree_id: str
    message: str
    timestamp: str
    author: dict[str, Any]
    committer: dict[str, Any]
    added: list[str] = Field(default_factory=list)
    removed: list[str] = Field(default_factory=list)
    modified: list[str] = Field(default_factory=list)


class Label(BaseModel):
    """Represents a GitHub label."""

    id: int
    node_id: str
    url: str
    name: str
    color: str
    default: bool
    description: str | None = None


class PullRequest(BaseModel):
    """Represents a GitHub pull request."""

    id: int
    node_id: str
    number: int
    state: str
    locked: bool
    title: str
    user: Actor
    body: str | None = None
    labels: list[Label] = Field(default_factory=list)
    assignees: list[Actor] = Field(default_factory=list)
    html_url: str
    diff_url: str
    patch_url: str
    base: dict[str, Any]
    head: dict[str, Any]
    merged: bool = False
    draft: bool = False


class Issue(BaseModel):
    """Represents a GitHub issue."""

    id: int
    node_id: str
    number: int
    state: str
    title: str
    user: Actor
    body: str | None = None
    labels: list[Label] = Field(default_factory=list)
    assignees: list[Actor] = Field(default_factory=list)
    html_url: str


class Comment(BaseModel):
    """Represents a comment on an issue or pull request."""

    id: int
    node_id: str
    user: Actor
    body: str
    html_url: str
    created_at: str
    updated_at: str


class WorkflowRun(BaseModel):
    """Represents a GitHub Actions workflow run."""

    id: int
    node_id: str
    name: str
    head_branch: str | None
    head_sha: str
    run_number: int
    event: str
    status: str | None
    conclusion: str | None
    workflow_id: int
    url: str
    html_url: str
    created_at: str
    updated_at: str


class BaseEvent(BaseModel):
    """Base class for all GitHub event payloads."""

    repository: Repository
    sender: Actor


class PushEvent(BaseEvent):
    """Event payload for push events."""

    ref: str
    before: str
    after: str
    commits: list[Commit] = Field(default_factory=list)
    head_commit: Commit | None = None
    pusher: dict[str, Any] | None = None
    forced: bool = False


class PullRequestEvent(BaseEvent):
    """Event payload for pull_request events."""

    action: str
    number: int
    pull_request: PullRequest


class IssueCommentEvent(BaseEvent):
    """Event payload for issue_comment events."""

    action: str
    issue: Issue
    comment: Comment


class WorkflowRunEvent(BaseEvent):
    """Event payload for workflow_run events."""

    action: str
    workflow_run: WorkflowRun
