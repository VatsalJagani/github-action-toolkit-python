import os
import re
import subprocess
import tempfile
from pathlib import Path
from types import TracebackType
from urllib.parse import urlparse, urlunparse

from git import Repo as GitRepo
from github import Github

from .print_messages import info, warning


class Repo:
    url: str | None
    repo_path: str
    repo: GitRepo
    base_branch: str
    cleanup: bool

    def __init__(
        self,
        url: str | None = None,
        path: str | None = None,
        cleanup: bool = False,
        depth: int | None = None,
        single_branch: bool = False,
    ):
        if not url and not path:
            raise ValueError("Either 'url' or 'path' must be provided")

        self.url = url
        self.repo_path = path or tempfile.mkdtemp(prefix="gitrepo_")

        if url:
            info(f"Cloning repository from {url} to {self.repo_path}")
            clone_kwargs = {}
            if depth is not None:
                clone_kwargs["depth"] = depth
            if single_branch:
                clone_kwargs["single_branch"] = single_branch
            self.repo = GitRepo.clone_from(url, self.repo_path, **clone_kwargs)  # pyright: ignore[reportUnknownArgumentType]
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

    def configure_safe_directory(self):
        """
        Configure the current repository as a git safe directory.
        Useful when running in containers or with different users.
        """
        info(f"Configuring safe directory for {self.repo_path}")
        try:
            subprocess.run(
                ["git", "config", "--global", "--add", "safe.directory", self.repo_path],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            warning(f"Failed to configure safe directory: {e.stderr}")

    def sparse_checkout_init(self, cone_mode: bool = True):
        """
        Initialize sparse checkout for the repository.

        :param cone_mode: Use cone mode (default True) for better performance
        """
        info("Initializing sparse checkout")
        self.repo.git.config("core.sparseCheckout", "true")
        if cone_mode:
            self.repo.git.config("core.sparseCheckoutCone", "true")

    def sparse_checkout_set(self, paths: list[str]):
        """
        Set sparse checkout paths.

        :param paths: List of paths to include in sparse checkout
        """
        info(f"Setting sparse checkout paths: {paths}")
        sparse_checkout_file = Path(self.repo_path) / ".git" / "info" / "sparse-checkout"
        sparse_checkout_file.parent.mkdir(parents=True, exist_ok=True)
        sparse_checkout_file.write_text("\n".join(paths) + "\n")
        self.repo.git.read_tree("-mu", "HEAD")

    def sparse_checkout_add(self, paths: list[str]):
        """
        Add paths to existing sparse checkout configuration.

        :param paths: List of paths to add
        """
        info(f"Adding sparse checkout paths: {paths}")
        sparse_checkout_file = Path(self.repo_path) / ".git" / "info" / "sparse-checkout"
        existing = ""
        if sparse_checkout_file.exists():
            existing = sparse_checkout_file.read_text()
        all_paths = set(existing.strip().split("\n") if existing.strip() else [])
        all_paths.update(paths)
        sparse_checkout_file.write_text("\n".join(sorted(all_paths)) + "\n")
        self.repo.git.read_tree("-mu", "HEAD")

    def submodule_init(self):
        """Initialize git submodules."""
        info("Initializing submodules")
        self.repo.git.submodule("init")

    def submodule_update(self, recursive: bool = False, remote: bool = False):
        """
        Update git submodules.

        :param recursive: Update submodules recursively
        :param remote: Update to latest remote commit
        """
        info("Updating submodules")
        args: list[str] = ["update"]
        if recursive:
            args.append("--recursive")
        if remote:
            args.append("--remote")
        self.repo.git.submodule(*args)

    def configure_gpg_signing(self, key_id: str | None = None, program: str | None = None):
        """
        Configure GPG signing for commits.

        :param key_id: GPG key ID to use for signing (optional)
        :param program: GPG program path (optional)
        """
        info("Configuring GPG signing")
        config_writer = self.repo.config_writer()
        config_writer.set_value("commit", "gpgsign", "true")
        if key_id:
            config_writer.set_value("user", "signingkey", key_id)
        if program:
            config_writer.set_value("gpg", "program", program)
        config_writer.release()

    def configure_ssh_signing(self, key_path: str | None = None):
        """
        Configure SSH signing for commits.

        :param key_path: Path to SSH key for signing (optional)
        """
        info("Configuring SSH signing")
        config_writer = self.repo.config_writer()
        config_writer.set_value("gpg", "format", "ssh")
        config_writer.set_value("commit", "gpgsign", "true")
        if key_path:
            config_writer.set_value("user", "signingkey", key_path)
        config_writer.release()

    def set_remote_url(self, remote: str, url: str, token: str | None = None):
        """
        Set or update remote URL with optional token authentication.

        :param remote: Remote name (e.g., 'origin')
        :param url: Remote URL
        :param token: Authentication token to embed in URL (optional)
        """
        if token:
            # Parse URL and inject token for HTTPS URLs
            parsed = urlparse(url)
            if parsed.scheme == "https" and parsed.hostname == "github.com":
                # Inject token into GitHub URL
                auth_url = urlunparse(
                    (
                        parsed.scheme,
                        f"x-access-token:{token}@{parsed.hostname}",
                        parsed.path,
                        parsed.params,
                        parsed.query,
                        parsed.fragment,
                    )
                )
                info(f"Setting remote {remote} with authentication")
                self.repo.git.remote("set-url", remote, auth_url)
            else:
                info(f"Setting remote {remote} to {url}")
                self.repo.git.remote("set-url", remote, url)
        else:
            info(f"Setting remote {remote} to {url}")
            self.repo.git.remote("set-url", remote, url)

    def create_tag(self, tag: str, message: str | None = None, signed: bool = False):
        """
        Create a git tag.

        :param tag: Tag name
        :param message: Tag message (creates annotated tag if provided)
        :param signed: Create a signed tag
        """
        info(f"Creating tag: {tag}")
        args: list[str] = []
        if signed:
            args.append("-s")
        elif message:
            args.append("-a")
        args.append(tag)
        if message:
            args.extend(["-m", message])
        self.repo.git.tag(*args)

    def list_tags(self, pattern: str | None = None) -> list[str]:
        """
        List tags in the repository.

        :param pattern: Optional pattern to filter tags
        :returns: List of tag names
        """
        args = ["-l"]
        if pattern:
            args.append(pattern)
        result = self.repo.git.tag(*args)
        return [tag.strip() for tag in result.split("\n") if tag.strip()]

    def push_tag(self, tag: str, remote: str = "origin"):
        """
        Push a specific tag to remote.

        :param tag: Tag name
        :param remote: Remote name (default: 'origin')
        """
        info(f"Pushing tag {tag} to {remote}")
        self.repo.git.push(remote, tag)

    def push_all_tags(self, remote: str = "origin"):
        """
        Push all tags to remote.

        :param remote: Remote name (default: 'origin')
        """
        info(f"Pushing all tags to {remote}")
        self.repo.git.push(remote, "--tags")

    def delete_tag(self, tag: str, remote: bool = False, remote_name: str = "origin"):
        """
        Delete a tag.

        :param tag: Tag name
        :param remote: Also delete from remote
        :param remote_name: Remote name (default: 'origin')
        """
        info(f"Deleting tag: {tag}")
        self.repo.git.tag("-d", tag)
        if remote:
            info(f"Deleting tag {tag} from {remote_name}")
            self.repo.git.push(remote_name, "--delete", tag)

    def get_latest_tag(self) -> str | None:
        """
        Get the most recent tag.

        :returns: Latest tag name or None if no tags exist
        """
        try:
            return self.repo.git.describe("--tags", "--abbrev=0")
        except Exception:  # noqa: BLE001
            return None

    def extract_changelog_section(
        self, changelog_path: str = "CHANGELOG.md", version: str | None = None
    ) -> str:
        """
        Extract a specific version section from a changelog file.

        :param changelog_path: Path to CHANGELOG.md relative to repo root
        :param version: Version to extract (defaults to Unreleased section)
        :returns: Changelog text for the version
        """
        changelog_file = Path(self.repo_path) / changelog_path
        if not changelog_file.exists():
            warning(f"Changelog file not found: {changelog_path}")
            return ""

        content = changelog_file.read_text()
        lines = content.split("\n")

        # Find the section for the requested version
        target = version or "Unreleased"
        section_lines: list[str] = []
        in_section = False
        header_pattern = re.compile(r"^##\s+")

        for line in lines:
            if header_pattern.match(line):
                if target in line:
                    in_section = True
                    continue  # Skip the header line
                elif in_section:
                    # We've hit the next section, stop
                    break
            elif in_section:
                section_lines.append(line)

        return "\n".join(section_lines).strip()

    def prepare_release(
        self,
        version: str,
        changelog_path: str = "CHANGELOG.md",
        create_tag_flag: bool = True,
        tag_message: str | None = None,
    ) -> dict[str, str]:
        """
        Helper for preparing a release.

        :param version: Version number (e.g., 'v1.0.0')
        :param changelog_path: Path to CHANGELOG.md
        :param create_tag_flag: Whether to create a tag
        :param tag_message: Message for the tag (defaults to changelog section)
        :returns: Dictionary with 'version', 'changelog', and optionally 'tag'
        """
        info(f"Preparing release for version {version}")

        # Extract changelog
        changelog = self.extract_changelog_section(changelog_path, version)
        if not changelog:
            changelog = self.extract_changelog_section(changelog_path, "Unreleased")

        result = {"version": version, "changelog": changelog}

        # Create tag if requested
        if create_tag_flag:
            message = tag_message or changelog or f"Release {version}"
            self.create_tag(version, message=message)
            result["tag"] = version

        return result

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
