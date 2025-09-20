import os
import re
import tempfile
from typing import Optional, Union

from git import Repo as GitRepo
from github import Github

from .print_messages import info


class Repo:
    def __init__(self, url: Optional[str] = None, path: Optional[str] = None):
        if not url and not path:
            raise ValueError("Either 'url' or 'path' must be provided")

        self.url = url
        self.repo_path = path or tempfile.mkdtemp(prefix="gitrepo_")

        if url:
            info(f"Cloning repository from {url} to {self.repo_path}")
            self.repo = GitRepo.clone_from(url, self.repo_path)
        else:
            info(f"Using existing repository at {self.repo_path}")
            self.repo = GitRepo(path)

        self.base_branch = self.repo.active_branch.name

    def __enter__(self):
        self.configure_git()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Optional cleanup
        pass

    def configure_git(self):
        config_writer = self.repo.config_writer()
        config_writer.set_value(
            "user", "name", os.environ.get("GIT_AUTHOR_NAME", "github-actions[bot]")
        )
        config_writer.set_value(
            "user",
            "email",
            os.environ.get("GIT_AUTHOR_EMAIL", "github-actions[bot]@users.noreply.github.com"),
        )
        config_writer.release()

    def get_current_branch(self) -> str:
        return self.repo.active_branch.name

    def create_new_branch(self, branch_name: str):
        info(f"Creating new branch: {branch_name}")
        self.repo.git.checkout("-b", branch_name)

    def add(self, file_path: str):
        info(f"Adding file: {file_path}")
        self.repo.git.add(file_path)

    def commit(self, message: str):
        info(f"Committing with message: {message}")
        self.repo.git.commit("-m", message)

    def add_all_and_commit(self, message: str):
        info("Adding all changes and committing")
        self.repo.git.add(all=True)
        self.repo.git.commit("-m", message)

    def push(self, remote: str = "origin", branch: Optional[str] = None):
        branch = branch or self.get_current_branch()
        info(f"Pushing to {remote}/{branch}")
        self.repo.git.push(remote, branch)

    def pull(self, remote: str = "origin", branch: Optional[str] = None):
        branch = branch or self.get_current_branch()
        info(f"Pulling from {remote}/{branch}")
        self.repo.git.pull(remote, branch)

    def create_pr(
        self,
        github_token: Union[str, None] = None,
        title: Union[str, None] = None,
        body: Union[str, None] = "",
        head: Union[str, None] = None,
        base: Union[str, None] = None,
    ) -> str:
        """
        Creates a pull request on GitHub.

        :param github_token: GitHub token with repo access (optional, defaults to env variable)
        :param title: Title for the PR (optional, uses last commit message)
        :param body: Body for the PR (optional)
        :param head: Source branch for the PR (optional, uses current branch)
        :param base: Target branch for the PR (optional, uses original base branch)
        :returns: URL of the created PR
        """

        # 1. Get GitHub token
        token = github_token or os.environ.get("GITHUB_TOKEN")
        if not token:
            raise ValueError("GitHub token not provided and GITHUB_TOKEN not set in environment.")

        # 2. Infer repo name from remote
        origin_url = self.repo.remotes.origin.url
        # Convert SSH or HTTPS URL to "owner/repo"
        match = re.search(r"(github\.com[:/])(.+?)(\.git)?$", origin_url)
        if not match:
            raise ValueError(f"Cannot extract repo name from remote URL: {origin_url}")
        repo_name = match.group(2)

        # 3. Use last commit message as PR title
        if not title:
            title = self.repo.head.commit.message.strip()

        # 4. Use current branch as head
        if not head:
            head = self.repo.active_branch.name

        # 5. Use base branch from original branch at init
        if not base:
            base = self.base_branch or "main"  # fallback if not set during init

        # 6. Create PR using PyGithub
        github = Github(token)
        repo = github.get_repo(repo_name)
        pr = repo.create_pull(title=title, body=body, head=head, base=base)

        return pr.html_url
