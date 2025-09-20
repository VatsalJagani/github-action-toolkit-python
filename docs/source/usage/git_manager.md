Git and GitHub Repo related Functions
================

### **`Repo(url=None, path=None)` Class**

Initializes the Git repository with this class.

Either url or path parameter is required.

If url is provided, the repo will be cloned into a temp directory. And you can access the path of the repository with `repo.repo_path` variable.

If path is provided, the existing local repo will be used.

**example:**

```python
>> from github_action_toolkit.git_manager import Repo

>> with Repo(url="https://github.com/user/repo.git") as repo:
>>     print(repo.get_current_branch())

# Output:
# main
```

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

### **`Repo.create_pr(github_token, repo_name, title, body, head, base="main")`**

Creates a pull request on GitHub.

Parameters:

github_token: GitHub token with repo scope.

repo_name: The repo in the format "owner/repo".

title: Title of the pull request.

body: Description body for the pull request.

head: The name of the branch with your changes.

base: The branch you want to merge into (default is "main").

**example:**

```python
>> pr_url = repo.create_pr(
>>     github_token=os.getenv("GITHUB_TOKEN"),
>>     repo_name="myuser/myrepo",
>>     title="Auto PR",
>>     body="This PR was created automatically.",
>>     head="feature/auto-update",
>>     base="main"
>> )

>> print(pr_url)

# Output:
# https://github.com/myuser/myrepo/pull/42
```
