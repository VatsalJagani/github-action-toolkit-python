GitHub Action Event Payload
=============

## Overview

The event payload module provides tools to work with GitHub Actions event data, including:

- Raw event payload access
- Strongly typed event models using Pydantic
- Convenience helper functions for common event operations

More details: [GitHub Actions Event Payload](https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads)

## Raw Event Payload

### **`event_payload()`**

Get GitHub Event payload that triggered the workflow as a dictionary.

**example:**

```python
from github_action_toolkit import event_payload

payload = event_payload()
# Output:
# {"action": "opened", "number": 1, "pull_request": {...}, "repository": {...}, "sender": {...}}
```

### **`get_event_name()`**

Get the name of the event that triggered the workflow.

**example:**

```python
from github_action_toolkit import get_event_name

event_name = get_event_name()
# Returns: "push", "pull_request", "issue_comment", etc.
```

## Typed Event Models

### **`get_typed_event()`**

Parse the event payload into a strongly typed Pydantic model based on the event type.

Supported event types:
- `push` → `PushEvent`
- `pull_request` / `pull_request_target` → `PullRequestEvent`
- `issue_comment` → `IssueCommentEvent`
- `workflow_run` → `WorkflowRunEvent`

**example:**

```python
from github_action_toolkit import get_typed_event, PushEvent, PullRequestEvent

event = get_typed_event()

if isinstance(event, PushEvent):
    print(f"Push to {event.ref}")
    print(f"Commits: {len(event.commits)}")
elif isinstance(event, PullRequestEvent):
    print(f"PR #{event.number}: {event.pull_request.title}")
    print(f"Action: {event.action}")
```

### Event Model Classes

The following typed models are available:

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

## Convenience Helpers

### **`is_pr()`**

Check if the current event is a pull request event.

**example:**

```python
from github_action_toolkit import is_pr

if is_pr():
    print("This is a pull request event")
```

### **`get_pr_number()`**

Get the pull request number for PR events.

**example:**

```python
from github_action_toolkit import get_pr_number

pr_number = get_pr_number()
if pr_number:
    print(f"PR number: {pr_number}")
```

### **`head_ref()`**

Get the head reference for the event.

- For push events: returns the ref being pushed to
- For pull request events: returns the head branch

**example:**

```python
from github_action_toolkit import head_ref

ref = head_ref()
print(f"Head ref: {ref}")
```

### **`base_ref()`**

Get the base reference for pull request events.

**example:**

```python
from github_action_toolkit import base_ref

ref = base_ref()
if ref:
    print(f"Base ref: {ref}")
```

### **`get_changed_files()`**

Get the list of changed files for push events.

**example:**

```python
from github_action_toolkit import get_changed_files

files = get_changed_files()
for file in files:
    print(f"Changed: {file}")
```

### **`get_labels()`**

Get the list of labels for pull request or issue events.

**example:**

```python
from github_action_toolkit import get_labels

labels = get_labels()
if "bug" in labels:
    print("This is a bug fix")
```

## Complete Example

```python
from github_action_toolkit import (
    get_event_name,
    get_typed_event,
    is_pr,
    get_pr_number,
    head_ref,
    base_ref,
    get_labels,
    get_changed_files,
    PushEvent,
    PullRequestEvent,
)

# Get event information
event_name = get_event_name()
print(f"Event: {event_name}")

# Use typed event models
event = get_typed_event()

if isinstance(event, PushEvent):
    print(f"Push to {event.ref}")
    print(f"Before: {event.before}")
    print(f"After: {event.after}")
    
    files = get_changed_files()
    print(f"Changed files: {', '.join(files)}")

elif isinstance(event, PullRequestEvent):
    print(f"PR #{event.number}: {event.pull_request.title}")
    print(f"Action: {event.action}")
    print(f"Head: {head_ref()}")
    print(f"Base: {base_ref()}")
    
    labels = get_labels()
    print(f"Labels: {', '.join(labels)}")

# Use helper functions
if is_pr():
    pr_num = get_pr_number()
    print(f"Working on PR #{pr_num}")
```
