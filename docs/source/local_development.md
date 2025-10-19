# Local Development and Testing

This guide covers tools and practices for developing and testing GitHub Actions locally.

## Local Development Simulator

The `local_simulator` module provides utilities to simulate GitHub Actions environment locally, allowing you to test your actions without pushing to GitHub.

### Basic Usage

```python
from github_action_toolkit import simulate_github_action, SimulatorConfig

config = SimulatorConfig(
    repository="myorg/myrepo",
    inputs={"name": "World", "greeting": "Hello"}
)

with simulate_github_action(config) as sim:
    import github_action_toolkit as gat
    
    # Your action code here
    name = gat.get_user_input("name")
    greeting = gat.get_user_input("greeting")
    
    gat.info(f"{greeting}, {name}!")
    gat.set_output("message", f"{greeting}, {name}!")
    
    # Access results within context
    print(sim.outputs)  # {"message": "Hello, World!"}
```

### Configuration Options

The `SimulatorConfig` class allows you to customize the simulated environment:

```python
config = SimulatorConfig(
    repository="owner/repo",           # Repository name
    ref="refs/heads/main",             # Git ref
    sha="abc123...",                   # Commit SHA
    actor="test-user",                 # Actor username
    workflow="test-workflow",          # Workflow name
    action="test-action",              # Action name
    run_id="1",                        # Run ID
    run_number="1",                    # Run number
    job="test-job",                    # Job name
    event_name="push",                 # Event type
    inputs={"key": "value"},           # Action inputs
    env_vars={"CUSTOM": "value"},      # Additional env vars
)
```

### Convenience Function

For simple use cases, use `run_action_locally`:

```python
from github_action_toolkit import run_action_locally, SimulatorConfig

def my_action():
    import github_action_toolkit as gat
    name = gat.get_user_input("name")
    gat.set_output("greeting", f"Hello, {name}!")

config = SimulatorConfig(inputs={"name": "World"})
result = run_action_locally(my_action, config)

print(result["outputs"])   # {"greeting": "Hello, World!"}
print(result["summary"])   # Job summary content
print(result["state"])     # State values
```

### Accessing Results

The simulator provides easy access to all outputs generated during action execution:

```python
with simulate_github_action(config) as sim:
    # Run your action code
    gat.set_output("result", "success")
    gat.append_job_summary("# Build Summary\n\nAll tests passed!")
    gat.save_state("build_time", "2025-10-19")
    
    # Access results
    print(sim.outputs)      # {"result": "success"}
    print(sim.summary)      # Job summary markdown
    print(sim.state)        # {"build_time": "2025-10-19"}
    print(sim.env_vars)     # Environment variables set
    print(sim.paths)        # Paths added to PATH
```

## Testing Best Practices

### Property-Based Testing

The project uses [Hypothesis](https://hypothesis.readthedocs.io/) for property-based testing to ensure robustness:

```python
from hypothesis import given
from hypothesis import strategies as st
import github_action_toolkit as gat

@given(st.text())
def test_escape_data_never_crashes(text):
    """Escaping should never raise an exception."""
    result = gat.print_messages.escape_data(text)
    assert isinstance(result, str)
```

### Snapshot Testing

The project uses [Syrupy](https://github.com/tophat/syrupy) for snapshot testing of formatted output:

```python
def test_job_summary_formatting(snapshot):
    """Ensure job summary format remains consistent."""
    result = generate_summary()
    assert result == snapshot
```

To update snapshots after intentional changes:
```bash
uv run pytest --snapshot-update
```

## CI Matrix Testing

The project CI tests across multiple Python versions and operating systems:

- Python versions: 3.11, 3.12, 3.13
- Operating systems: Ubuntu, macOS, Windows

This ensures compatibility across all supported platforms.

## Running Tests Locally

```bash
# Run all tests
make test

# Run specific test file
uv run pytest tests/test_local_simulator.py

# Run with coverage
uv run pytest --cov=github_action_toolkit

# Run property-based tests with more examples
uv run pytest tests/test_property_based.py --hypothesis-show-statistics
```

## Example: Testing a Complete Action

Here's a complete example of testing a GitHub Action locally:

```python
from github_action_toolkit import simulate_github_action, SimulatorConfig
import github_action_toolkit as gat

def my_github_action():
    """Example GitHub Action."""
    # Get inputs
    name = gat.get_user_input("name") or "World"
    verbose = gat.get_user_input_as("verbose", bool, default_value=False)
    
    # Log execution
    if verbose:
        gat.debug(f"Processing for {name}")
    
    # Perform action
    message = f"Hello, {name}!"
    gat.info(message)
    
    # Set outputs
    gat.set_output("message", message)
    gat.set_output("timestamp", "2025-10-19")
    
    # Add job summary
    gat.append_job_summary(f"# Action Complete\n\nGreeted {name} successfully!")

# Test the action locally
config = SimulatorConfig(
    repository="test/repo",
    inputs={
        "name": "Developer",
        "verbose": "true"
    }
)

with simulate_github_action(config) as sim:
    my_github_action()
    
    # Verify results
    assert sim.outputs["message"] == "Hello, Developer!"
    assert "Greeted Developer successfully" in sim.summary
    
print("✓ Action tested successfully!")
```
