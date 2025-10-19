Git and GitHub Repo related Functions
================

### **`Repo(url: str = None, path: str = None, cleanup: bool = False, depth: int = None, single_branch: bool = False)` Class**

Initializes the Git repository with this class.

Either url or path parameter is required.

If url is provided, the repo will be cloned into a temp directory. And you can access the path of the repository with `repo.repo_path` variable.

If path is provided, the existing local repo will be used.

#### Parameters

- `url` (str, optional): URL of the Git repository to clone
- `path` (str, optional): Path to an existing local Git repository
- `cleanup` (bool, default=False): Enable cleanup mode (see below)
- `depth` (int, optional): Create a shallow clone with specified depth (faster clones)
- `single_branch` (bool, default=False): Clone only a single branch (faster clones)

#### Cleanup Mode (`cleanup=True`)

When `cleanup=True`, the repository is force-synchronized to the original base branch captured at construction time on both context entry and exit:

1. `git fetch --prune` (non-fatal if it fails)
2. Pre-sync: `git reset --hard` then `git clean -fdx` (clear local changes/untracked files)
3. Checkout base branch:
	- If `origin/<base_branch>` exists: `git checkout -B <base_branch> origin/<base_branch>`
	- Otherwise: `git checkout <base_branch>` (non-fatal; logs on failure)
4. Post-sync reset:
	- If `origin/<base_branch>` exists: `git reset --hard origin/<base_branch>` (falls back to `git reset --hard` on failure)
	- Otherwise: `git reset --hard`
5. Post-sync clean: `git clean -fdx` (removes untracked, directories, ignored files)
6. `git pull origin <base_branch>` (non-fatal)

This synchronization happens twice: once on `__enter__` (before your work) and once on `__exit__` (after your work), guaranteeing the repo is clean, on the base branch, and up to date. All steps are defensive: errors never raise, they only log.


**example:**

```python
>> from github_action_toolkit import Repo

>> with Repo(url="https://github.com/user/repo.git") as repo:
>>     print(repo.get_current_branch())

# Output:
# main
```

**Shallow clone example:**

```python
>> # Clone only the latest commit for faster CI workflows
>> with Repo(url="https://github.com/user/repo.git", depth=1, single_branch=True) as repo:
>>     print(f"Cloned to {repo.repo_path}")
```

## Basic Operations

### **`Repo.get_current_branch()`**

Returns the name of the currently active Git branch.

**example:**

```python
>> repo.get_current_branch()

# Output:
# feature/my-branch
```

### **`Repo.create_new_branch(branch_name)`**

Creates and checks out a new branch from the current branch.

**example:**

```python
>> repo.create_new_branch("feature/auto-update")
```

### **`Repo.add(file_path)`**

Stages a specific file for commit.

**example:**

```python
>> repo.add("README.md")
```

### **`Repo.commit(message)`**

Commits the currently staged files with the specified message.

**example:**

```python
>> repo.commit("Update README")
```

### **`Repo.add_all_and_commit(message)`**

Stages all changes in the repository and commits them with the given message.

**example:**

```python
>> repo.add_all_and_commit("Auto-update configuration files")
```

### **`Repo.push(remote="origin", branch=None)`**

Pushes the current branch to the specified remote (default is origin). If branch is not provided, pushes the currently active branch.

**example:**

```python
>> repo.push()
```

### **`Repo.pull(remote="origin", branch=None)`**

Pulls the latest changes for the current branch from the specified remote (default is origin). If branch is not provided, pulls the currently active branch.

**example:**

```python
>> repo.pull()
```

### **`Repo.create_pr(github_token=None, title=None, body=None, head=None, base=None)`**

Creates a pull request on GitHub.

This method automatically infers most of the required values based on the current repository state, making it ideal for use in GitHub Actions or automation scripts.

Parameters:

* github_token (optional):
GitHub token with repo scope.
If not provided, it will be read from the environment variable GITHUB_TOKEN.

* title (optional):
Title of the pull request.
If not provided, the latest commit message will be used.

* body (optional):
Description body for the pull request.
Defaults to an empty string.

* head (optional):
The name of the branch containing your changes.
If not provided, the current active branch will be used.

* base (optional):
The branch you want to merge into.
If not provided, it uses the branch that was active at the time the repo was cloned or opened.

**example:**

```python
>> pr_url = repo.create_pr(
>>     github_token=os.getenv("GITHUB_TOKEN"),
>>     title="Auto PR",
>>     body="This PR was created automatically.",
>>     head="feature/auto-update",
>>     base="main"
>> )

>> print(pr_url)

# Output:
# https://github.com/myuser/myrepo/pull/42
```

Or, using full automatic inference:

```python
>> pr_url = repo.create_pr()

>> print(pr_url)

# Output:
# https://github.com/myuser/myrepo/pull/42
```

## Advanced Git Operations

### **`Repo.configure_safe_directory()`**

Configures the current repository as a git safe directory. This is essential when running in containers or with different users to avoid "dubious ownership" errors.

**example:**

```python
>> repo.configure_safe_directory()
```

### **`Repo.sparse_checkout_init(cone_mode=True)`**

Initialize sparse checkout for the repository. Sparse checkout allows you to check out only specific paths from a repository, which is useful for large repositories.

**Parameters:**
- `cone_mode` (bool, default=True): Use cone mode for better performance

**example:**

```python
>> repo.sparse_checkout_init()
```

### **`Repo.sparse_checkout_set(paths)`**

Set the paths to include in sparse checkout.

**Parameters:**
- `paths` (list[str]): List of paths to include in sparse checkout

**example:**

```python
>> repo.sparse_checkout_set(["src/", "docs/", "README.md"])
```

### **`Repo.sparse_checkout_add(paths)`**

Add additional paths to the existing sparse checkout configuration.

**Parameters:**
- `paths` (list[str]): List of paths to add

**example:**

```python
>> repo.sparse_checkout_add(["tests/"])
```

**Complete sparse checkout example:**

```python
>> with Repo(url="https://github.com/user/large-repo.git") as repo:
>>     repo.sparse_checkout_init()
>>     repo.sparse_checkout_set(["src/", "docs/", "README.md"])
>>     # Now only src/, docs/, and README.md are checked out
```

### **`Repo.submodule_init()`**

Initialize git submodules in the repository.

**example:**

```python
>> repo.submodule_init()
```

### **`Repo.submodule_update(recursive=False, remote=False)`**

Update git submodules.

**Parameters:**
- `recursive` (bool, default=False): Update submodules recursively
- `remote` (bool, default=False): Update to latest remote commit

**example:**

```python
>> repo.submodule_update(recursive=True, remote=True)
```

### **`Repo.configure_gpg_signing(key_id=None, program=None)`**

Configure GPG signing for commits.

**Parameters:**
- `key_id` (str, optional): GPG key ID to use for signing
- `program` (str, optional): GPG program path

**example:**

```python
>> repo.configure_gpg_signing(key_id="ABC123DEF456", program="/usr/bin/gpg")
```

### **`Repo.configure_ssh_signing(key_path=None)`**

Configure SSH signing for commits (Git 2.34+).

**Parameters:**
- `key_path` (str, optional): Path to SSH key for signing

**example:**

```python
>> repo.configure_ssh_signing(key_path="/home/user/.ssh/id_ed25519.pub")
```

### **`Repo.set_remote_url(remote, url, token=None)`**

Set or update remote URL with optional token authentication.

**Parameters:**
- `remote` (str): Remote name (e.g., 'origin')
- `url` (str): Remote URL
- `token` (str, optional): Authentication token to embed in URL

**example:**

```python
>> import os
>> repo.set_remote_url("origin", "https://github.com/user/repo.git", token=os.getenv("GITHUB_TOKEN"))
```

## Tag Management

### **`Repo.create_tag(tag, message=None, signed=False)`**

Create a git tag.

**Parameters:**
- `tag` (str): Tag name
- `message` (str, optional): Tag message (creates annotated tag if provided)
- `signed` (bool, default=False): Create a signed tag

**example:**

```python
>> # Lightweight tag
>> repo.create_tag("v1.0.0")

>> # Annotated tag
>> repo.create_tag("v1.0.0", message="Release version 1.0.0")

>> # Signed tag
>> repo.create_tag("v1.0.0", message="Release version 1.0.0", signed=True)
```

### **`Repo.list_tags(pattern=None)`**

List tags in the repository.

**Parameters:**
- `pattern` (str, optional): Optional pattern to filter tags

**Returns:**
- `list[str]`: List of tag names

**example:**

```python
>> tags = repo.list_tags()
>> print(tags)
# Output: ['v1.0.0', 'v1.1.0', 'v2.0.0']

>> v1_tags = repo.list_tags(pattern="v1.*")
>> print(v1_tags)
# Output: ['v1.0.0', 'v1.1.0']
```

### **`Repo.push_tag(tag, remote="origin")`**

Push a specific tag to remote.

**Parameters:**
- `tag` (str): Tag name
- `remote` (str, default="origin"): Remote name

**example:**

```python
>> repo.push_tag("v1.0.0")
```

### **`Repo.push_all_tags(remote="origin")`**

Push all tags to remote.

**Parameters:**
- `remote` (str, default="origin"): Remote name

**example:**

```python
>> repo.push_all_tags()
```

### **`Repo.delete_tag(tag, remote=False, remote_name="origin")`**

Delete a tag locally and optionally from remote.

**Parameters:**
- `tag` (str): Tag name
- `remote` (bool, default=False): Also delete from remote
- `remote_name` (str, default="origin"): Remote name

**example:**

```python
>> # Delete locally only
>> repo.delete_tag("v1.0.0")

>> # Delete locally and from remote
>> repo.delete_tag("v1.0.0", remote=True)
```

### **`Repo.get_latest_tag()`**

Get the most recent tag.

**Returns:**
- `str | None`: Latest tag name or None if no tags exist

**example:**

```python
>> latest = repo.get_latest_tag()
>> print(latest)
# Output: v2.0.0
```

## Release Preparation

### **`Repo.extract_changelog_section(changelog_path="CHANGELOG.md", version=None)`**

Extract a specific version section from a changelog file (Keep a Changelog format).

**Parameters:**
- `changelog_path` (str, default="CHANGELOG.md"): Path to CHANGELOG.md relative to repo root
- `version` (str, optional): Version to extract (defaults to Unreleased section)

**Returns:**
- `str`: Changelog text for the version

**example:**

```python
>> # Extract unreleased changes
>> unreleased = repo.extract_changelog_section()
>> print(unreleased)

>> # Extract specific version
>> v1_changes = repo.extract_changelog_section(version="v1.0.0")
>> print(v1_changes)
```

### **`Repo.prepare_release(version, changelog_path="CHANGELOG.md", create_tag_flag=True, tag_message=None)`**

Helper for preparing a release with changelog extraction and automatic tagging.

**Parameters:**
- `version` (str): Version number (e.g., 'v1.0.0')
- `changelog_path` (str, default="CHANGELOG.md"): Path to CHANGELOG.md
- `create_tag_flag` (bool, default=True): Whether to create a tag
- `tag_message` (str, optional): Message for the tag (defaults to changelog section)

**Returns:**
- `dict[str, str]`: Dictionary with 'version', 'changelog', and optionally 'tag'

**example:**

```python
>> release_info = repo.prepare_release("v1.0.0")
>> print(f"Version: {release_info['version']}")
>> print(f"Changelog: {release_info['changelog']}")
>> print(f"Tag: {release_info['tag']}")
```

**Complete release workflow example:**

```python
>> import os
>> from github_action_toolkit import Repo

>> with Repo(path=".") as repo:
>>     # Configure signing
>>     repo.configure_gpg_signing(key_id=os.getenv("GPG_KEY_ID"))
>>     
>>     # Prepare release
>>     release_info = repo.prepare_release("v1.0.0")
>>     
>>     # Push tag to remote
>>     repo.push_tag("v1.0.0")
>>     
>>     print(f"Released {release_info['version']}")
>>     print(f"Changelog:\n{release_info['changelog']}")
```

