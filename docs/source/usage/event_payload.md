# GitHub Event Payload

Access event data from GitHub Actions workflow triggers.

## Overview

The `EventPayload` class provides a typed interface for accessing GitHub Actions event data from workflow triggers like push, pull_request, release, and more. It includes strongly typed event models using Pydantic and convenience helper methods for common operations.

Learn more: [GitHub Actions Event Payload](https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads)

## API Reference

### `EventPayload()`

The `EventPayload` class provides a unified interface for accessing GitHub Actions event data.

### `get_payload()`

Get GitHub Event payload that triggered the workflow as a dictionary.

**example:**

```python
from github_action_toolkit import EventPayload

event = EventPayload()
payload = event.get_payload()
# Output:
# {"action": "opened", "number": 1, "pull_request": {...}, "repository": {...}, "sender": {...}}
```

### `get_event_name()`

Get the name of the event that triggered the workflow.

**example:**

```python
from github_action_toolkit import EventPayload

event = EventPayload()
event_name = event.get_event_name()
# Returns: "push", "pull_request", "issue_comment", etc.
```

## Typed Event Models

### `get_typed_event()`

Parse the event payload into a strongly typed Pydantic model based on the event type.

Supported event types:
- `push` → `PushEvent`
- `pull_request` / `pull_request_target` → `PullRequestEvent`
- `issue_comment` → `IssueCommentEvent`
- `workflow_run` → `WorkflowRunEvent`

**example:**

```python
from github_action_toolkit import EventPayload
from github_action_toolkit.event_models import PushEvent, PullRequestEvent

event = EventPayload()
typed_event = event.get_typed_event()

if isinstance(typed_event, PushEvent):
    print(f"Push to {typed_event.ref}")
    print(f"Commits: {len(typed_event.commits)}")
elif isinstance(typed_event, PullRequestEvent):
    print(f"PR #{typed_event.number}: {typed_event.pull_request.title}")
    print(f"Action: {typed_event.action}")
```

### Event Model Classes

The following typed models are available from `github_action_toolkit.event_models`:

- `PushEvent` - Push events with commits, refs, and change information
- `PullRequestEvent` - Pull request events with PR details, labels, reviewers
- `IssueCommentEvent` - Issue and PR comment events
- `WorkflowRunEvent` - Workflow run events

Supporting models:
- `Actor` - GitHub user or organization
- `Repository` - Repository information
- `Commit` - Git commit details
- `Label` - Issue/PR labels
- `PullRequest` - Pull request details
- `Issue` - Issue details
- `Comment` - Comment on issue or PR
- `WorkflowRun` - Workflow run details

**Note:** These models are imported from `github_action_toolkit.event_models`:

```python
from github_action_toolkit.event_models import (
    PushEvent,
    PullRequestEvent,
    Actor,
    Repository,
    # ... other models
)
```

## Convenience Helpers

### `is_pr()`

Check if the current event is a pull request event.

**example:**

```python
from github_action_toolkit import EventPayload

event = EventPayload()
if event.is_pr():
    print("This is a pull request event")
```

### `get_pr_number()`

Get the pull request number for PR events.

**example:**

```python
from github_action_toolkit import EventPayload

event = EventPayload()
pr_number = event.get_pr_number()
if pr_number:
    print(f"PR number: {pr_number}")
```

### `head_ref()`

Get the head reference for the event.

- For push events: returns the ref being pushed to
- For pull request events: returns the head branch

**example:**

```python
from github_action_toolkit import EventPayload

event = EventPayload()
ref = event.head_ref()
print(f"Head ref: {ref}")
```

### `base_ref()`

Get the base reference for pull request events.

**example:**

```python
from github_action_toolkit import EventPayload

event = EventPayload()
ref = event.base_ref()
if ref:
    print(f"Base ref: {ref}")
```

### `get_changed_files()`

Get the list of changed files for push events.

**example:**

```python
from github_action_toolkit import EventPayload

event = EventPayload()
files = event.get_changed_files()
for file in files:
    print(f"Changed: {file}")
```

### `get_labels()`

Get the list of labels for pull request or issue events.

**example:**

```python
from github_action_toolkit import EventPayload

event = EventPayload()
labels = event.get_labels()
if "bug" in labels:
    print("This is a bug fix")
```

## Complete Example

```python
from github_action_toolkit import EventPayload
from github_action_toolkit.event_models import PushEvent, PullRequestEvent

# Create event instance
event = EventPayload()

# Get event information
event_name = event.get_event_name()
print(f"Event: {event_name}")

# Use typed event models
typed_event = event.get_typed_event()

if isinstance(typed_event, PushEvent):
    print(f"Push to {typed_event.ref}")
    print(f"Before: {typed_event.before}")
    print(f"After: {typed_event.after}")
    
    files = event.get_changed_files()
    print(f"Changed files: {', '.join(files)}")

elif isinstance(typed_event, PullRequestEvent):
    print(f"PR #{typed_event.number}: {typed_event.pull_request.title}")
    print(f"Action: {typed_event.action}")
    print(f"Head: {event.head_ref()}")
    print(f"Base: {event.base_ref()}")
    
    labels = event.get_labels()
    print(f"Labels: {', '.join(labels)}")

# Use helper methods
if event.is_pr():
    pr_num = event.get_pr_number()
    print(f"Working on PR #{pr_num}")
```
