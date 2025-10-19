# pyright: reportPrivateUsage=false
# pyright: reportUnknownMemberType=false

"""Tests for the local GitHub Actions simulator."""

import json

import github_action_toolkit as gat
from github_action_toolkit.local_simulator import (
    SimulatorConfig,
    simulate_github_action,
)


def test_simulate_github_action_basic() -> None:
    """Test basic simulation of GitHub Actions environment."""
    config = SimulatorConfig(
        repository="test/repo",
        actor="test-user",
        inputs={"input1": "value1"},
    )

    with simulate_github_action(config) as sim:
        # Check environment variables are set
        import os

        assert os.getenv("GITHUB_REPOSITORY") == "test/repo"
        assert os.getenv("GITHUB_ACTOR") == "test-user"
        assert os.getenv("INPUT_INPUT1") == "value1"

        # Write some outputs
        gat.set_output("test_output", "test_value")
        gat.append_job_summary("# Test Summary")

        # Check outputs were captured (inside context)
        assert sim.outputs["test_output"] == "test_value"
        assert "# Test Summary" in sim.summary


def test_simulate_github_action_with_inputs() -> None:
    """Test simulator with multiple inputs."""
    config = SimulatorConfig(
        inputs={
            "name": "World",
            "greeting-type": "friendly",
            "count": "5",
        }
    )

    with simulate_github_action(config):
        import os

        assert os.getenv("INPUT_NAME") == "World"
        assert os.getenv("INPUT_GREETING_TYPE") == "friendly"
        assert os.getenv("INPUT_COUNT") == "5"


def test_simulate_github_action_event_payload() -> None:
    """Test that event payload is created and accessible."""
    config = SimulatorConfig(repository="owner/repo", ref="refs/heads/main")

    with simulate_github_action(config) as sim:
        # Read event payload
        event_data = json.loads(sim.event_path.read_text())

        assert event_data["repository"]["full_name"] == "owner/repo"
        assert event_data["ref"] == "refs/heads/main"


def test_simulator_multi_line_output() -> None:
    """Test that multi-line outputs are properly captured."""
    config = SimulatorConfig()

    with simulate_github_action(config) as sim:
        gat.set_output("multiline", "line1\nline2\nline3")
        assert sim.outputs["multiline"] == "line1\nline2\nline3"


def test_simulator_state() -> None:
    """Test that state values are captured."""
    config = SimulatorConfig()

    with simulate_github_action(config) as sim:
        gat.save_state("test_state", "state_value")
        assert sim.state["test_state"] == "state_value"


def test_simulator_env_vars() -> None:
    """Test custom environment variables in config."""
    config = SimulatorConfig(
        env_vars={"CUSTOM_VAR": "custom_value", "ANOTHER_VAR": "another_value"}
    )

    with simulate_github_action(config):
        import os

        assert os.getenv("CUSTOM_VAR") == "custom_value"
        assert os.getenv("ANOTHER_VAR") == "another_value"


def test_simulator_restores_environment() -> None:
    """Test that original environment is restored after simulation."""
    import os

    # Set a test variable
    original_value = os.getenv("GITHUB_REPOSITORY")

    config = SimulatorConfig(repository="test/repo")

    with simulate_github_action(config):
        assert os.getenv("GITHUB_REPOSITORY") == "test/repo"

    # Check environment is restored
    assert os.getenv("GITHUB_REPOSITORY") == original_value


def test_simulator_summary_multiple_appends() -> None:
    """Test multiple summary appends."""
    config = SimulatorConfig()

    with simulate_github_action(config) as sim:
        gat.append_job_summary("# Title")
        gat.append_job_summary("## Section 1")
        gat.append_job_summary("- Item 1")
        gat.append_job_summary("- Item 2")

        summary = sim.summary
        assert "# Title" in summary
        assert "## Section 1" in summary
        assert "- Item 1" in summary
        assert "- Item 2" in summary
