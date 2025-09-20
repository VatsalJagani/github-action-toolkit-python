import os
import tempfile
from typing import Optional
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

    def __enter__(self):
        self.configure_git()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Optional cleanup
        pass


    def configure_git(self):
        config_writer = self.repo.config_writer()
        config_writer.set_value("user", "name", os.environ.get("GIT_AUTHOR_NAME", "github-actions[bot]"))
        config_writer.set_value("user", "email", os.environ.get("GIT_AUTHOR_EMAIL", "github-actions[bot]@users.noreply.github.com"))
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
        github_token: str,
        repo_name: str,
        title: str,
        body: str,
        head: str,
        base: str = "main"
    ):
        """
        Creates a pull request on GitHub using PyGithub.
        - github_token: GitHub token (with repo scope)
        - repo_name: 'owner/repo'
        - head: branch name with your changes (e.g., 'fix/my-bug')
        - base: branch to merge into (default 'main')
        """
        info(f"Creating PR from {head} to {base} on {repo_name}")
        gh = Github(github_token)
        repo = gh.get_repo(repo_name)
        pr = repo.create_pull(title=title, body=body, head=head, base=base)
        info(f"Pull request created: {pr.html_url}")
        return pr.html_url
