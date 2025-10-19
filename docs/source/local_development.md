# Local Development and Testing for Custom GitHub Actions

This guide shows you how to test your custom GitHub Actions locally without pushing to GitHub, using the local development simulator.

## Why Use the Local Simulator?

When developing custom GitHub Actions, you typically need to:
1. Write your action code
2. Push to GitHub
3. Trigger the workflow
4. Wait for results
5. Repeat if there are bugs

The local simulator lets you skip steps 2-4 and test instantly on your machine!

## Local Development Simulator

The `local_simulator` module simulates the GitHub Actions environment locally, allowing you to test your custom actions without pushing to GitHub.

### Basic Usage

Here's a simple example of testing a custom action that greets users:

```python
from github_action_toolkit import simulate_github_action, SimulatorConfig
import github_action_toolkit as gat

# Your custom action code
def my_greeting_action():
    name = gat.get_user_input("name") or "World"
    greeting = gat.get_user_input("greeting") or "Hello"
    
    message = f"{greeting}, {name}!"
    gat.info(message)
    gat.set_output("message", message)
    gat.append_job_summary(f"# Greeting\n\nSaid: {message}")

# Test it locally
config = SimulatorConfig(
    repository="myorg/myrepo",
    inputs={"name": "Alice", "greeting": "Hi"}
)

with simulate_github_action(config) as sim:
    my_greeting_action()
    
    # Check results
    print(sim.outputs)  # {"message": "Hi, Alice!"}
    print(sim.summary)  # Job summary content
```

### Configuration Options

The `SimulatorConfig` class allows you to customize the simulated environment to match your action's needs:

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
    event_name="push",                 # Event type (push, pull_request, etc.)
    inputs={"key": "value"},           # Action inputs
    env_vars={"CUSTOM": "value"},      # Additional environment variables
)
```

### Accessing Results

The simulator captures all outputs, summaries, and state from your action:

```python
with simulate_github_action(config) as sim:
    # Run your action code
    gat.set_output("result", "success")
    gat.append_job_summary("# Build Summary\n\nAll tests passed!")
    gat.save_state("build_time", "2025-10-19")
    
    # Access results within the context
    print(sim.outputs)      # {"result": "success"}
    print(sim.summary)      # Job summary markdown
    print(sim.state)        # {"build_time": "2025-10-19"}
    print(sim.env_vars)     # Environment variables set
    print(sim.paths)        # Paths added to PATH
```

## Real-World Example: Docker Build Action

Here's a realistic example of testing a custom action that builds and pushes Docker images:

```python
from github_action_toolkit import simulate_github_action, SimulatorConfig
import github_action_toolkit as gat

def docker_build_action():
    """
    Custom action that builds and pushes a Docker image.
    
    Inputs:
    - dockerfile: Path to Dockerfile (default: Dockerfile)
    - image_name: Name of the Docker image
    - image_tag: Tag for the Docker image (default: latest)
    - push: Whether to push to registry (default: true)
    """
    # Get inputs
    dockerfile = gat.get_user_input("dockerfile") or "Dockerfile"
    image_name = gat.get_user_input("image_name")
    image_tag = gat.get_user_input("image_tag") or "latest"
    should_push = gat.get_user_input_as("push", bool, default_value=True)
    
    if not image_name:
        gat.error("image_name input is required!")
        return
    
    # Build image
    full_image = f"{image_name}:{image_tag}"
    gat.start_group("Building Docker Image")
    gat.info(f"Building {full_image} from {dockerfile}")
    
    # Simulate docker build (in real action, you'd run docker commands)
    gat.info("Step 1/5 : FROM python:3.11-slim")
    gat.info("Step 2/5 : WORKDIR /app")
    gat.info("Step 3/5 : COPY . .")
    gat.info("Step 4/5 : RUN pip install -r requirements.txt")
    gat.info("Step 5/5 : CMD ['python', 'app.py']")
    gat.info("✓ Successfully built image")
    gat.end_group()
    
    # Push image (if enabled)
    if should_push:
        gat.start_group("Pushing Docker Image")
        gat.info(f"Pushing {full_image} to registry")
        gat.info("✓ Successfully pushed image")
        gat.end_group()
    else:
        gat.info("Skipping push (push=false)")
    
    # Set outputs
    gat.set_output("image", full_image)
    gat.set_output("image_name", image_name)
    gat.set_output("image_tag", image_tag)
    
    # Create job summary
    gat.append_job_summary("# Docker Build Summary")
    gat.append_job_summary(f"- **Image:** `{full_image}`")
    gat.append_job_summary(f"- **Dockerfile:** `{dockerfile}`")
    gat.append_job_summary(f"- **Pushed:** {'✅ Yes' if should_push else '❌ No'}")
    
    gat.notice(f"Docker image {full_image} built successfully!")

# Test the action locally
config = SimulatorConfig(
    repository="mycompany/myapp",
    ref="refs/heads/main",
    actor="developer",
    inputs={
        "dockerfile": "Dockerfile",
        "image_name": "mycompany/myapp",
        "image_tag": "v1.2.3",
        "push": "true"
    }
)

print("=" * 60)
print("Testing Docker Build Action Locally")
print("=" * 60)

with simulate_github_action(config) as sim:
    docker_build_action()
    
    # Verify outputs
    print("\n" + "=" * 60)
    print("Action Results:")
    print("=" * 60)
    print(f"Image: {sim.outputs.get('image')}")
    print(f"Image Name: {sim.outputs.get('image_name')}")
    print(f"Image Tag: {sim.outputs.get('image_tag')}")
    print("\nJob Summary:")
    print(sim.summary)

print("\n✓ Action tested successfully!")
```

## Real-World Example: Release Notes Generator

Here's another example of a custom action that generates release notes:

```python
from github_action_toolkit import simulate_github_action, SimulatorConfig
import github_action_toolkit as gat

def release_notes_action():
    """
    Custom action that generates release notes from commit messages.
    
    Inputs:
    - version: Release version (e.g., v1.2.3)
    - previous_version: Previous version for comparison
    - include_authors: Include commit authors (default: true)
    """
    version = gat.get_user_input("version")
    previous_version = gat.get_user_input("previous_version")
    include_authors = gat.get_user_input_as("include_authors", bool, default_value=True)
    
    if not version:
        gat.error("version input is required!")
        return
    
    gat.info(f"Generating release notes for {version}")
    
    # In a real action, you'd fetch commits from git/GitHub API
    # Here we simulate with sample data
    commits = [
        {"message": "Add new authentication feature", "author": "alice"},
        {"message": "Fix memory leak in processor", "author": "bob"},
        {"message": "Update documentation", "author": "charlie"},
        {"message": "Improve error handling", "author": "alice"},
    ]
    
    # Generate release notes
    notes = [f"# Release {version}\n"]
    
    if previous_version:
        notes.append(f"Changes since {previous_version}:\n")
    
    notes.append("## Changes\n")
    for commit in commits:
        line = f"- {commit['message']}"
        if include_authors:
            line += f" (@{commit['author']})"
        notes.append(line)
    
    release_notes = "\n".join(notes)
    
    # Set outputs
    gat.set_output("release_notes", release_notes)
    gat.set_output("version", version)
    gat.set_output("commit_count", str(len(commits)))
    
    # Add to job summary
    gat.append_job_summary(release_notes)
    
    gat.notice(f"Generated release notes for {version} with {len(commits)} commits")

# Test the action
config = SimulatorConfig(
    repository="mycompany/myproject",
    inputs={
        "version": "v1.2.3",
        "previous_version": "v1.2.2",
        "include_authors": "true"
    }
)

with simulate_github_action(config) as sim:
    release_notes_action()
    
    print("Release Notes Generated:")
    print(sim.outputs.get("release_notes"))
    print(f"\nVersion: {sim.outputs.get('version')}")
    print(f"Commits: {sim.outputs.get('commit_count')}")
```

## Testing Different Scenarios

You can easily test edge cases and different scenarios:

```python
# Test with missing required inputs
config_missing = SimulatorConfig(
    repository="myorg/myrepo",
    inputs={}  # No inputs provided
)

with simulate_github_action(config_missing) as sim:
    my_action()
    # Verify error handling works

# Test with different event types
config_pr = SimulatorConfig(
    repository="myorg/myrepo",
    event_name="pull_request",
    inputs={"name": "PR Author"}
)

with simulate_github_action(config_pr) as sim:
    my_action()
    # Verify PR-specific behavior

# Test with custom environment variables
config_env = SimulatorConfig(
    repository="myorg/myrepo",
    inputs={"name": "World"},
    env_vars={
        "CUSTOM_API_URL": "https://api.example.com",
        "DEBUG": "true"
    }
)

with simulate_github_action(config_env) as sim:
    my_action()
    # Verify environment variable handling
```

## Tips for Testing Custom Actions

1. **Test Early and Often**: Run your action locally before pushing to verify basic functionality
2. **Test Edge Cases**: Use the simulator to test error conditions, missing inputs, and edge cases
3. **Verify Outputs**: Always check that outputs, summaries, and state are set correctly
4. **Test Different Events**: If your action behaves differently for different GitHub events (push, pull_request, etc.), test each one
5. **Use Realistic Data**: Configure the simulator with realistic repository names, refs, and inputs that match your actual use case

## Debugging Your Action

The simulator preserves all GitHub Actions logging, so you can see exactly what your action outputs:

```python
with simulate_github_action(config) as sim:
    # Your action code with debug logging
    gat.debug("Starting action")
    gat.info("Processing input")
    gat.warning("This might take a while")
    my_action()
    gat.debug("Action complete")
    
    # All logs are displayed in console as they would be in GitHub Actions
```

## Next Steps

Once you've tested your action locally and verified it works:

1. Commit your action code
2. Push to GitHub
3. Create or update your action's `action.yml` file
4. Test in a real workflow
5. Publish your action to the GitHub Marketplace (optional)

The local simulator helps you catch bugs early and iterate faster, making custom action development much more efficient!


## Testing Actions

### Local Testing with Simulator

```python
from github_action_toolkit import simulate_github_action, SimulatorConfig

def test_greeting_action():
    """Test the greeting action locally."""
    config = SimulatorConfig(
        inputs={'name': 'Test User'},
        repository='testorg/testrepo'
    )
    
    with simulate_github_action(config) as sim:
        # Import and run your action
        from action import main
        main()
    
    # Verify outputs
    assert sim.outputs['greeting'] == 'Hello, Test User!'
    
    # Verify summary was created
    assert 'Greeting' in sim.summary
```

### Integration Testing

```python
import pytest
from github_action_toolkit import simulate_github_action, SimulatorConfig

@pytest.fixture
def github_env():
    """Provide simulated GitHub environment."""
    config = SimulatorConfig(repository='test/repo')
    with simulate_github_action(config) as sim:
        yield sim

def test_action_with_inputs(github_env):
    """Test action with specific inputs."""
    # Your action code runs here
    from action import process_inputs
    result = process_inputs()
    
    assert result is not None
    assert github_env.outputs['status'] == 'success'
```
