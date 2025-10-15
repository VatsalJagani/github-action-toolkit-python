import os
import re
import tempfile
from types import TracebackType

from git import Repo as GitRepo
from github import Github

from .print_messages import info, warning


class Repo:
    url: str | None
    repo_path: str
    repo: GitRepo
    base_branch: str
    cleanup: bool

    def __init__(self, url: str | None = None, path: str | None = None, cleanup: bool = False):
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
        self.cleanup = cleanup

    def __enter__(self):
        self.configure_git()

        if not self.cleanup:
            return self
        self._sync_to_base_branch()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ):
        if not self.cleanup:
            return
        # Ensure we leave the repo on the base branch and fully up-to-date as well.
        self._sync_to_base_branch()

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

    def push(self, remote: str = "origin", branch: str | None = None):
        branch = branch or self.get_current_branch()
        info(f"Pushing to {remote}/{branch}")
        self.repo.git.push(remote, branch)

    def pull(self, remote: str = "origin", branch: str | None = None):
        branch = branch or self.get_current_branch()
        info(f"Pulling from {remote}/{branch}")
        self.repo.git.pull(remote, branch)

    def create_pr(
        self,
        github_token: str | None = None,
        title: str | None = None,
        body: str = "",
        head: str | None = None,
        base: str | None = None,
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
            raw_message = self.repo.head.commit.message
            if isinstance(raw_message, bytes):
                raw_message = raw_message.decode()
            title = raw_message.strip()
            if not title:
                raise ValueError("No commit message found for PR title.")

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

    def _sync_to_base_branch(self) -> None:
        """
        Synchronize working tree to the recorded base branch:
        - fetch --prune
        - checkout <base>
        - reset --hard (to origin/<base> when available, else local HEAD)
        - clean -fdx
        - pull origin <base>

        Non-fatal on individual step failures; logs and proceeds.
        """
        info(
            f"Synchronizing repository to base branch '{self.base_branch}' (fetch, checkout, reset, clean, pull)"
        )
        try:
            self.repo.git.fetch("--prune")
        except Exception as exc:  # noqa: BLE001
            warning(f"Fetch failed: {exc}")

        current_base = self.base_branch

        # Pre-clean to avoid checkout failures due to local modifications/untracked files
        try:
            self.repo.git.reset("--hard")
        except Exception as exc:  # noqa: BLE001
            info(f"Pre-checkout local hard reset failed: {exc}")
        try:
            self.repo.git.clean("-fdx")
        except Exception as exc:  # noqa: BLE001
            info(f"Pre-checkout clean failed: {exc}")

        # Resolve origin and available remote refs safely
        origin = None
        # Prefer attribute access if available (works with mocks/tests)
        try:
            origin = getattr(self.repo.remotes, "origin", None)
        except Exception:  # noqa: BLE001
            origin = None
        if origin is None:
            try:
                for remote in self.repo.remotes or []:
                    if getattr(remote, "name", None) == "origin":
                        origin = remote
                        break
            except Exception:  # noqa: BLE001
                origin = None
        remote_ref = f"origin/{current_base}"
        remote_branches: set[str] = {ref.name for ref in origin.refs} if origin else set()

        # Checkout base branch; if remote ref exists, prefer forcing base to track it
        try:
            if remote_ref in remote_branches:
                # Ensure local base points to remote commit and is checked out
                self.repo.git.checkout("-B", current_base, remote_ref)
            else:
                self.repo.git.checkout(current_base)
        except Exception as exc:  # noqa: BLE001
            info(f"Checkout of base branch '{current_base}' failed: {exc}")

        # Post-checkout sync/reset to ensure exact commit alignment
        if remote_ref in remote_branches:
            try:
                self.repo.git.reset("--hard", remote_ref)
            except Exception as exc:  # noqa: BLE001
                info(f"Hard reset to {remote_ref} failed: {exc}; falling back to local HEAD")
                try:
                    self.repo.git.reset("--hard")
                except Exception as exc:  # noqa: BLE001
                    info(f"Fallback local hard reset failed: {exc}")
        else:
            info(f"Remote ref {remote_ref} not found; performing local hard reset")
            try:
                self.repo.git.reset("--hard")
            except Exception as exc:  # noqa: BLE001
                info(f"Local hard reset failed: {exc}")

        # Final clean to remove any residuals after branch switch
        try:
            self.repo.git.clean("-fdx")
        except Exception as exc:  # noqa: BLE001
            info(f"Final clean failed: {exc}")
        try:
            self.repo.git.pull("origin", current_base)
        except Exception as exc:  # noqa: BLE001
            info(f"Pull failed: {exc}")
