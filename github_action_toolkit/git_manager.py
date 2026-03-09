from __future__ import annotations

import os
import re
import subprocess
import tempfile
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from types import TracebackType
from typing import Any, TypeVar, cast
from urllib.parse import urlparse, urlunparse

from git import Repo as GitPythonRepo
from github import Github

from .exceptions import (
    ConfigurationError,
    GitAuthenticationError,
    GitCloneError,
    GitHubAPIError,
    GitNetworkError,
    GitOperationError,
    GitReferenceError,
)
from .print_messages import info, warning

T = TypeVar("T")


@dataclass(frozen=True)
class OperationMetadata:
    """Metadata for an operation execution useful for observability/debugging."""

    attempts: int
    retries: int
    elapsed_ms: int
    success: bool


class Repo:
    url: str | None
    repo_path: str
    repo: GitPythonRepo
    base_branch: str
    cleanup: bool
    retry_attempts: int
    retry_backoff_seconds: float
    retry_backoff_multiplier: float
    clone_branch: str | None
    clone_ref: str | None
    clone_depth: int | None
    clone_single_branch: bool
    clone_no_checkout: bool
    github_token: str | None
    _custom_redactor: Callable[[str], str] | None
    _operation_metadata: dict[str, OperationMetadata]

    def __init__(
        self,
        url: str | None = None,
        path: str | None = None,
        cleanup: bool = False,
        depth: int | None = None,
        single_branch: bool = False,
        clone_branch: str | None = None,
        clone_ref: str | None = None,
        github_token: str | None = None,
        clone_no_checkout: bool = False,
        retry_attempts: int = 3,
        retry_backoff_seconds: float = 1.0,
        retry_backoff_multiplier: float = 2.0,
        redactor: Callable[[str], str] | None = None,
    ):
        """
        Initialize a Git repository manager.

        :param url: URL to clone from (e.g., https://github.com/owner/repo.git)
        :param path: Path to existing repository
        :param cleanup: Whether to sync to base branch on enter/exit
        :param depth: Depth for shallow clone (if cloning)
        :param single_branch: Whether to clone a single branch (if cloning)
        :param clone_branch: Branch to clone explicitly. Primarily clone-scoped, and also
            used as fallback in `_detect_base_branch()` when active branch cannot be read.
        :param clone_ref: Branch/tag/SHA to checkout after clone. Primarily clone-scoped,
            and also used as fallback in `_detect_base_branch()`.
        :param github_token: Optional GitHub token. Used for clone authentication and as
            class-level default for `create_pr()`. If omitted, falls back to `GITHUB_TOKEN`.
        :param clone_no_checkout: Clone without checking out HEAD
        :param retry_attempts: Number of attempts for clone/fetch/pull operations
        :param retry_backoff_seconds: Initial retry backoff in seconds
        :param retry_backoff_multiplier: Exponential backoff multiplier
        :param redactor: Optional callback to further redact sensitive text in errors
        :raises ConfigurationError: When neither url nor path is provided
        :raises GitOperationError: When repository operations fail
        """
        if not url and not path:
            raise ConfigurationError(
                "Either 'url' or 'path' must be provided. "
                "Provide a Git repository URL to clone or a path to an existing repository."
            )

        if retry_attempts < 1:
            raise ConfigurationError("retry_attempts must be >= 1")
        if retry_backoff_seconds < 0:
            raise ConfigurationError("retry_backoff_seconds must be >= 0")
        if retry_backoff_multiplier < 1:
            raise ConfigurationError("retry_backoff_multiplier must be >= 1")

        self.url = url
        self.repo_path = path or tempfile.mkdtemp(prefix="gitrepo_")
        self.retry_attempts = retry_attempts
        self.retry_backoff_seconds = retry_backoff_seconds
        self.retry_backoff_multiplier = retry_backoff_multiplier
        self.clone_branch = clone_branch
        self.clone_ref = clone_ref
        self.clone_depth = depth
        self.clone_single_branch = single_branch
        self.clone_no_checkout = clone_no_checkout
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN")
        self._custom_redactor = redactor
        self._operation_metadata = {}

        try:
            if url:
                redacted_url = self._redact_sensitive_text(url)
                info(f"Cloning repository from {redacted_url} to {self.repo_path}")
                self.repo = self._clone_repository(url)
            else:
                info(f"Using existing repository at {self.repo_path}")
                if path is None:
                    raise ConfigurationError("path must be provided when url is not set")
                self.repo = GitPythonRepo(path)
        except Exception as e:
            if isinstance(e, GitOperationError):
                raise
            error = self._classify_git_error(e, context="initialize repository")
            raise error from e

        self.base_branch = self._detect_base_branch()
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
        try:
            self._run_with_retry(
                operation_name="pull",
                operation=lambda: self.repo.git.pull(remote, branch),
            )
        except Exception as exc:
            raise self._classify_git_error(exc, context=f"pull {remote}/{branch}") from exc

    def fetch(self, remote: str = "origin", prune: bool = True):
        """Fetch updates from the remote, optionally pruning deleted refs."""
        info(f"Fetching from {remote}")
        args = [remote]
        if prune:
            args.insert(0, "--prune")
        try:
            self._run_with_retry(
                operation_name="fetch",
                operation=lambda: self.repo.git.fetch(*args),
            )
        except Exception as exc:
            raise self._classify_git_error(exc, context=f"fetch {remote}") from exc

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
        :raises ConfigurationError: When GitHub token is not available
        :raises GitHubAPIError: When PR creation fails
        """

        # 1. Get GitHub token
        token = github_token or self.github_token or os.environ.get("GITHUB_TOKEN")
        if not token:
            raise ConfigurationError(
                "GitHub token not provided and GITHUB_TOKEN not set in environment. "
                "Provide a token via the github_token parameter or set GITHUB_TOKEN."
            )

        # 2. Infer repo name from remote
        try:
            origin_url = self.repo.remotes.origin.url
        except Exception as e:
            raise GitOperationError(
                f"Failed to get origin remote URL: {self._redact_sensitive_text(str(e))}. "
                "Ensure the repository has an 'origin' remote configured."
            ) from e

        # Convert SSH or HTTPS URL to "owner/repo"
        match = re.search(r"(github\.com[:/])(.+?)(\.git)?$", origin_url)
        if not match:
            raise ConfigurationError(
                f"Cannot extract repo name from remote URL: {self._redact_sensitive_text(origin_url)}. "
                "Expected a GitHub URL like https://github.com/owner/repo.git"
            )
        repo_name = match.group(2)

        # 3. Use last commit message as PR title
        if not title:
            try:
                raw_message = self.repo.head.commit.message
                if isinstance(raw_message, bytes):
                    raw_message = raw_message.decode()
                title = raw_message.strip()
                if not title:
                    raise ConfigurationError(
                        "No commit message found for PR title. "
                        "Provide a title parameter or ensure the repository has commits."
                    )
            except Exception as e:
                raise GitOperationError(f"Failed to get commit message: {e}") from e

        # 4. Use current branch as head
        if not head:
            head = self.repo.active_branch.name

        # 5. Use base branch from original branch at init
        if not base:
            base = self.base_branch or "main"  # fallback if not set during init

        # 6. Create PR using PyGithub
        try:
            github = Github(login_or_token=token)
            repo = github.get_repo(repo_name)
            pr = repo.create_pull(title=title, body=body, head=head, base=base)
            return pr.html_url
        except Exception as e:
            raise GitHubAPIError(
                f"Failed to create pull request: {e}. "
                f"Ensure the token has permissions and branches exist (head: {head}, base: {base})."
            ) from e

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
            self.fetch(remote="origin", prune=True)
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
            self.pull("origin", current_base)
        except Exception as exc:  # noqa: BLE001
            info(f"Pull failed: {exc}")

    def get_operation_metadata(
        self, operation_name: str | None = None
    ) -> dict[str, dict[str, int | bool]] | dict[str, int | bool] | None:
        """
        Return operation metadata captured for retried operations.

        If `operation_name` is omitted, returns a dict for all tracked operations.
        """
        if operation_name is not None:
            metadata = self._operation_metadata.get(operation_name)
            return asdict(metadata) if metadata else None
        return {name: asdict(metadata) for name, metadata in self._operation_metadata.items()}

    def _clone_repository(self, url: str) -> GitPythonRepo:
        clone_kwargs: dict[str, object] = {}
        if self.clone_depth is not None:
            clone_kwargs["depth"] = self.clone_depth
        if self.clone_single_branch:
            clone_kwargs["single_branch"] = self.clone_single_branch
        if self.clone_branch:
            clone_kwargs["branch"] = self.clone_branch
        if self.clone_no_checkout:
            clone_kwargs["no_checkout"] = self.clone_no_checkout
        clone_kwargs_typed = cast(dict[str, Any], clone_kwargs)

        clone_url = self._build_authenticated_url(url)
        try:
            repo = self._run_with_retry(
                operation_name="clone",
                operation=lambda: GitPythonRepo.clone_from(
                    clone_url, self.repo_path, **clone_kwargs_typed
                ),
            )
        except Exception as exc:
            raise self._classify_git_error(exc, context="clone", default=GitCloneError) from exc

        if self.clone_ref:
            try:
                self._run_with_retry(
                    operation_name="checkout_ref",
                    operation=lambda: repo.git.checkout(self.clone_ref),
                )
            except Exception as exc:
                raise self._classify_git_error(
                    exc, context=f"checkout ref '{self.clone_ref}'"
                ) from exc
        return repo

    def _detect_base_branch(self) -> str:
        try:
            return self.repo.active_branch.name
        except Exception:  # noqa: BLE001
            if self.clone_branch:
                return self.clone_branch
            if self.clone_ref:
                return self.clone_ref
            return "main"

    def _run_with_retry(self, operation_name: str, operation: Callable[[], T]) -> T:
        total_attempts = self.retry_attempts
        started_at = time.perf_counter()

        last_exception: Exception | None = None
        for attempt in range(1, total_attempts + 1):
            try:
                result = operation()
                elapsed_ms = int((time.perf_counter() - started_at) * 1000)
                self._operation_metadata[operation_name] = OperationMetadata(
                    attempts=attempt,
                    retries=attempt - 1,
                    elapsed_ms=elapsed_ms,
                    success=True,
                )
                return result
            except Exception as exc:  # noqa: BLE001
                last_exception = exc
                if attempt >= total_attempts:
                    break
                backoff = self.retry_backoff_seconds * (
                    self.retry_backoff_multiplier ** (attempt - 1)
                )
                warning(
                    f"{operation_name} failed on attempt {attempt}/{total_attempts}: {self._redact_sensitive_text(str(exc))}. "
                    f"Retrying in {backoff:.2f}s"
                )
                time.sleep(backoff)

        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        self._operation_metadata[operation_name] = OperationMetadata(
            attempts=total_attempts,
            retries=max(total_attempts - 1, 0),
            elapsed_ms=elapsed_ms,
            success=False,
        )
        if last_exception is None:
            raise GitOperationError(f"Operation '{operation_name}' failed without an exception")
        raise last_exception

    def _build_authenticated_url(self, url: str) -> str:
        if not self.github_token:
            return url
        parsed = urlparse(url)
        if parsed.scheme == "https" and parsed.hostname == "github.com":
            return urlunparse(
                (
                    parsed.scheme,
                    f"x-access-token:{self.github_token}@{parsed.hostname}",
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment,
                )
            )
        return url

    def _redact_sensitive_text(self, text: str) -> str:
        redacted = text
        redacted = re.sub(r"(https?://)([^/@\s]+)@", r"\1***@", redacted)

        secrets = [
            self.github_token,
            os.environ.get("GITHUB_TOKEN"),
            os.environ.get("GH_TOKEN"),
        ]
        for secret in secrets:
            if secret:
                redacted = redacted.replace(secret, "***")

        if self._custom_redactor:
            redacted = self._custom_redactor(redacted)
        return redacted

    def _classify_git_error(
        self,
        exc: Exception,
        *,
        context: str,
        default: type[GitOperationError] = GitOperationError,
    ) -> GitOperationError:
        message = self._redact_sensitive_text(str(exc))
        lowered = message.lower()

        auth_patterns = (
            "authentication failed",
            "could not read username",
            "permission denied",
            "access denied",
            "repository not found",
            "http basic: access denied",
            "403",
            "401",
        )
        network_patterns = (
            "timed out",
            "timeout",
            "connection reset",
            "connection refused",
            "temporary failure",
            "network is unreachable",
            "could not resolve host",
            "failed to connect",
        )
        ref_patterns = (
            "pathspec",
            "did not match any file",
            "couldn't find remote ref",
            "unknown revision",
            "not something we can merge",
            "reference is not a tree",
        )

        if any(pattern in lowered for pattern in auth_patterns):
            return GitAuthenticationError(f"Failed to {context}: {message}")
        if any(pattern in lowered for pattern in network_patterns):
            return GitNetworkError(f"Failed to {context}: {message}")
        if any(pattern in lowered for pattern in ref_patterns):
            return GitReferenceError(f"Failed to {context}: {message}")
        return default(f"Failed to {context}: {message}")


# Alias for backward compatibility and convenience
GitRepo = Repo
