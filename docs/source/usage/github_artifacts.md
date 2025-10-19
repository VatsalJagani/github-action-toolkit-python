# GitHub Artifacts

Upload and download workflow artifacts for sharing data between jobs.

## Overview

The `GitHubArtifacts` class provides robust artifact management with upload/download capabilities, pattern matching, integrity checks, and error handling.

## API Reference

### `GitHubArtifacts(github_token=None, github_repo=None)`

Initializes the artifact manager for GitHub Actions artifact operations.

Both parameters are optional but environment variables for it needs to be present GITHUB_TOKEN and GITHUB_REPOSITORY respectively.

**example:**

```python
>> from github_action_toolkit import GitHubArtifacts
>> artifacts = GitHubArtifacts()
```

### `GitHubArtifacts.get_artifacts(current_run_only=False, name_pattern=None)`

Returns a list of GitHub Actions artifacts for the current repository with optional filtering.

* `current_run_only` (optional): If True, only returns artifacts from the current workflow run (GITHUB_RUN_ID must be set in env).
* `name_pattern` (optional): Filter by name pattern using wildcards (e.g., "test-*" or "*-results")

**example:**

```python
>> artifacts = artifacts.get_artifacts(current_run_only=True)
>> for artifact in artifacts:
>>     print(artifact.name)

# Output:
# running-tests
# publish-release

>> # Filter by pattern
>> test_artifacts = artifacts.get_artifacts(name_pattern="test-*")
>> for artifact in test_artifacts:
>>     print(artifact.name)

# Output:
# test-results
# test-coverage
```

### `GitHubArtifacts.get_artifact(artifact_id)`

Fetches a specific artifact by its ID.

**example:**

```python
>> artifact = artifacts.get_artifact(artifact_id=123456)
>> print(artifact.name)

# Output
# running-tests
```

### `GitHubArtifacts.upload_artifact(name, paths=None, patterns=None, root_dir=None, retention_days=None, verify_checksum=True, max_retries=3)`

Upload files as an artifact with pattern matching, compression, and integrity checks.

* `name`: Artifact name
* `paths` (optional): List of file/directory paths to include
* `patterns` (optional): List of glob patterns (e.g., ["*.log", "build/**/*.js"])
* `root_dir` (optional): Root directory for relative paths (defaults to current dir)
* `retention_days` (optional): Days to retain artifact (GitHub default applies if not set)
* `verify_checksum` (optional): Calculate and return SHA-256 checksum (default: True)
* `max_retries` (optional): Maximum retry attempts on failure (default: 3)

Returns a dictionary with artifact info including checksum.

**example:**

```python
>> # Upload files matching patterns
>> result = artifacts.upload_artifact(
>>     name="test-results",
>>     patterns=["*.xml", "coverage/**"],
>>     retention_days=7
>> )

# Output:
# Artifact 'test-results' uploaded successfully.

>> print(result)
# {'name': 'test-results', 'size': '12345', 'checksum': 'abc123...'}

>> # Upload specific paths
>> result = artifacts.upload_artifact(
>>     name="build-output",
>>     paths=["dist/", "build/app.js"]
>> )
```

### `GitHubArtifacts.download_artifact(artifact, is_extract=False, extract_dir=None, verify_checksum=False, expected_checksum=None, max_retries=3)`

Downloads a given artifact as a zip file with optional extraction and integrity verification.

* `artifact`: The artifact object (from get_artifacts() or get_artifact()).
* `is_extract` (optional): If True, extracts the contents of the zip.
* `extract_dir` (optional): Directory to extract to. Defaults to artifact_<artifact.name>.
* `verify_checksum` (optional): Calculate and print checksum for verification (default: False)
* `expected_checksum` (optional): Expected SHA-256 checksum to verify against
* `max_retries` (optional): Maximum retry attempts on failure (default: 3)

**example:**

```python
>> file_path = artifacts.download_artifact(artifact)

# Output:
# Artifact 'running-tests' downloaded successfully.

>> # Download with checksum verification
>> file_path = artifacts.download_artifact(
>>     artifact,
>>     verify_checksum=True,
>>     expected_checksum="abc123..."
>> )

# Output:
# Artifact 'running-tests' downloaded successfully.
# Checksum verified: abc123...
```

Extracting it:

```python
>> folder = artifacts.download_artifact(artifact, is_extract=True)

# Output:
# Artifact 'running-tests' downloaded successfully.
# Folder 'artifact_running-tests' created with extracted contents.
```

### `GitHubArtifacts.delete_artifact(artifact, max_retries=3)`

Deletes the given artifact from the repository with retry logic for robustness.

* `artifact`: The artifact object to delete.
* `max_retries` (optional): Maximum retry attempts on failure (default: 3)

Returns True if deleted successfully, otherwise False.

**example:**

```python
>> result = artifacts.delete_artifact(artifact)

# Output:
# Artifact 123456 (test-logs) deleted successfully.
```

## Features

The artifact management system includes:

* **Pattern Glob Support**: Use wildcards to select files for upload (e.g., `*.log`, `build/**/*.js`)
* **Compression**: Automatic ZIP compression with optimized settings
* **Multi-file Streaming**: Efficient handling of multiple files
* **Integrity Checks**: SHA-256 checksums for upload and download verification
* **Retention Configuration**: Set custom retention periods for artifacts
* **Retry Logic**: Automatic retry with exponential backoff for transient failures
* **Error Handling**: Robust handling of large files and edge cases with detailed error messages


## Artifact Patterns

### Uploading Test Results

```python
from pathlib import Path
from github_action_toolkit import GitHubArtifacts, info

def upload_test_results(results_dir: Path):
    """Upload all test result files as artifacts."""
    artifacts = GitHubArtifacts()
    
    # Upload with pattern matching
    artifacts.upload_artifact(
        name='test-results',
        paths=[results_dir],
        retention_days=30
    )
    
    info(f'Uploaded test results from {results_dir}')
```

### Downloading from Previous Run

```python
from github_action_toolkit import GitHubArtifacts, info

def download_previous_artifact(artifact_name: str, dest: str):
    """Download artifact from previous workflow run."""
    artifacts = GitHubArtifacts()
    
    # Get latest artifact with this name
    artifact_list = artifacts.get_artifacts(name_pattern=artifact_name)
    
    if not artifact_list:
        info(f'No artifact found: {artifact_name}')
        return None
    
    latest = artifact_list[0]
    artifacts.download_artifact(latest.id, dest)
    info(f'Downloaded {artifact_name} to {dest}')
    return dest
```

### Conditional Artifact Upload

```python
from github_action_toolkit import GitHubArtifacts, get_user_input_as

def upload_artifacts_if_enabled():
    """Only upload artifacts if configured."""
    upload_artifacts = get_user_input_as(
        'upload-artifacts',
        bool,
        default_value=True
    )
    
    if not upload_artifacts:
        info('Artifact upload disabled')
        return
    
    artifacts = GitHubArtifacts()
    artifacts.upload_artifact(
        name='build-output',
        paths=['dist/']
    )
```
