"""
Local development simulator for GitHub Actions.

This module provides utilities to simulate GitHub Actions environment locally,
allowing developers to test their actions without pushing to GitHub.
"""

import json
import os
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SimulatorConfig:
    """Configuration for the local GitHub Actions simulator."""

    repository: str = "owner/repo"
    ref: str = "refs/heads/main"
    sha: str = "0000000000000000000000000000000000000000"
    actor: str = "test-user"
    workflow: str = "test-workflow"
    action: str = "test-action"
    run_id: str = "1"
    run_number: str = "1"
    job: str = "test-job"
    event_name: str = "push"
    event_path: Path | None = None
    workspace: Path | None = None
    inputs: dict[str, str] = field(default_factory=dict)
    env_vars: dict[str, str] = field(default_factory=dict)


@contextmanager
def simulate_github_action(config: SimulatorConfig | None = None):
    """
    Context manager that simulates GitHub Actions environment locally.

    Creates temporary files for outputs, summaries, and environment variables,
    and sets up environment variables that mimic GitHub Actions.

    Usage:
    ```python
    from github_action_toolkit.local_simulator import simulate_github_action, SimulatorConfig

    config = SimulatorConfig(
        repository="myorg/myrepo",
        inputs={"input1": "value1", "input2": "value2"}
    )

    with simulate_github_action(config) as sim:
        # Your action code here
        import github_action_toolkit as gat
        gat.info("Running action locally")
        gat.set_output("result", "success")

    # After context, check outputs
    print(sim.outputs)  # {"result": "success"}
    print(sim.summary)  # Job summary content
    ```
    """
    if config is None:
        config = SimulatorConfig()

    # Create temporary directory for GitHub Actions files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create temporary files
        output_file = tmppath / "output.txt"
        env_file = tmppath / "env.txt"
        summary_file = tmppath / "summary.txt"
        state_file = tmppath / "state.txt"
        path_file = tmppath / "path.txt"

        # Create files
        output_file.touch()
        env_file.touch()
        summary_file.touch()
        state_file.touch()
        path_file.touch()

        # Setup event payload
        event_path = config.event_path
        if event_path is None:
            event_path = tmppath / "event.json"
            default_event = {
                "repository": {
                    "name": config.repository.split("/")[-1]
                    if "/" in config.repository
                    else config.repository,
                    "owner": {
                        "login": config.repository.split("/")[0]
                        if "/" in config.repository
                        else "owner"
                    },
                    "full_name": config.repository,
                },
                "ref": config.ref,
                "sha": config.sha,
                "pusher": {"name": config.actor},
            }
            event_path.write_text(json.dumps(default_event, indent=2))

        # Setup workspace
        workspace = config.workspace or Path.cwd()

        # Prepare environment variables
        env_vars = {
            "GITHUB_WORKFLOW": config.workflow,
            "GITHUB_RUN_ID": config.run_id,
            "GITHUB_RUN_NUMBER": config.run_number,
            "GITHUB_ACTION": config.action,
            "GITHUB_ACTIONS": "true",
            "GITHUB_ACTOR": config.actor,
            "GITHUB_REPOSITORY": config.repository,
            "GITHUB_EVENT_NAME": config.event_name,
            "GITHUB_EVENT_PATH": str(event_path),
            "GITHUB_WORKSPACE": str(workspace),
            "GITHUB_SHA": config.sha,
            "GITHUB_REF": config.ref,
            "GITHUB_JOB": config.job,
            "GITHUB_OUTPUT": str(output_file),
            "GITHUB_ENV": str(env_file),
            "GITHUB_STEP_SUMMARY": str(summary_file),
            "GITHUB_STATE": str(state_file),
            "GITHUB_PATH": str(path_file),
        }

        # Add inputs as environment variables
        for key, value in config.inputs.items():
            env_key = f"INPUT_{key.upper().replace(' ', '_').replace('-', '_')}"
            env_vars[env_key] = value

        # Add custom environment variables
        env_vars.update(config.env_vars)

        # Store original environment
        original_env = dict(os.environ)

        try:
            # Set environment variables
            os.environ.update(env_vars)

            # Create simulator result object
            simulator = SimulatorResult(
                output_file=output_file,
                env_file=env_file,
                summary_file=summary_file,
                state_file=state_file,
                path_file=path_file,
                event_path=event_path,
                workspace=workspace,
            )

            yield simulator

        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)


@dataclass
class SimulatorResult:
    """
    Results from a simulated GitHub Action run.

    Provides easy access to outputs, environment variables, summaries, etc.
    """

    output_file: Path
    env_file: Path
    summary_file: Path
    state_file: Path
    path_file: Path
    event_path: Path
    workspace: Path

    @property
    def outputs(self) -> dict[str, str]:
        """Parse and return all outputs set during the action."""
        content = self.output_file.read_text()
        if not content:
            return {}

        outputs: dict[str, str] = {}
        lines = content.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i]
            if "<<__ENV_DELIMITER__" in line:
                # Multi-line output format
                key = line.split("<<")[0]
                i += 1
                value_lines: list[str] = []
                while i < len(lines) and lines[i] != "__ENV_DELIMITER__":
                    value_lines.append(lines[i])
                    i += 1
                raw_value = "\n".join(value_lines)
                # Decode escaped characters
                decoded_value = (
                    raw_value.replace("%25", "%").replace("%0D", "\r").replace("%0A", "\n")
                )
                outputs[key] = decoded_value
            i += 1
        return outputs

    @property
    def env_vars(self) -> dict[str, str]:
        """Parse and return all environment variables set during the action."""
        content = self.env_file.read_text()
        if not content:
            return {}

        env_vars: dict[str, str] = {}
        lines = content.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i]
            if "<<__ENV_DELIMITER__" in line:
                # Multi-line format
                key = line.split("<<")[0]
                i += 1
                value_lines: list[str] = []
                while i < len(lines) and lines[i] != "__ENV_DELIMITER__":
                    value_lines.append(lines[i])
                    i += 1
                raw_value = "\n".join(value_lines)
                # Decode escaped characters
                decoded_value = (
                    raw_value.replace("%25", "%").replace("%0D", "\r").replace("%0A", "\n")
                )
                env_vars[key] = decoded_value
            elif "=" in line:
                # Simple key=value format
                key, value = line.split("=", 1)
                env_vars[key] = value
            i += 1
        return env_vars

    @property
    def summary(self) -> str:
        """Return the job summary content."""
        return self.summary_file.read_text()

    @property
    def state(self) -> dict[str, str]:
        """Parse and return all state values."""
        content = self.state_file.read_text()
        if not content:
            return {}

        state: dict[str, str] = {}
        lines = content.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i]
            if "<<__ENV_DELIMITER__" in line:
                key = line.split("<<")[0]
                i += 1
                value_lines: list[str] = []
                while i < len(lines) and lines[i] != "__ENV_DELIMITER__":
                    value_lines.append(lines[i])
                    i += 1
                raw_value = "\n".join(value_lines)
                # Decode escaped characters
                decoded_value = (
                    raw_value.replace("%25", "%").replace("%0D", "\r").replace("%0A", "\n")
                )
                state[key] = decoded_value
            i += 1
        return state

    @property
    def paths(self) -> list[str]:
        """Return paths added to PATH."""
        content = self.path_file.read_text()
        return [line for line in content.split("\n") if line.strip()]
