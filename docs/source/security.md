# Security Best Practices

Guidelines for building secure GitHub Actions using github-action-toolkit.

## Table of Contents

- [Input Validation](#input-validation)
- [Secrets Management](#secrets-management)
- [Dependency Security](#dependency-security)
- [Code Injection Prevention](#code-injection-prevention)
- [API Token Security](#api-token-security)
- [Environment Variable Safety](#environment-variable-safety)
- [Artifact Security](#artifact-security)
- [Network Security](#network-security)

## Input Validation

### Always Validate Inputs

Never trust user inputs directly. Validate, sanitize, and constrain all inputs:

```python
from github_action_toolkit import get_user_input, error
import re

def get_safe_branch_name() -> str:
    """Get and validate branch name input."""
    branch = get_user_input('branch') or 'main'
    
    # Only allow alphanumeric, dash, underscore, and forward slash
    if not re.match(r'^[a-zA-Z0-9/_-]+$', branch):
        error(
            f"Invalid branch name: {branch}. "
            "Only alphanumeric characters, dashes, underscores, "
            "and forward slashes are allowed.",
            title="Security: Invalid Input"
        )
        raise SystemExit(1)
    
    return branch
```

### Limit Input Length

Prevent resource exhaustion with length limits:

```python
from github_action_toolkit import get_user_input, error

MAX_DESCRIPTION_LENGTH = 1000

description = get_user_input('description') or ''
if len(description) > MAX_DESCRIPTION_LENGTH:
    error(
        f"Description too long: {len(description)} characters "
        f"(max: {MAX_DESCRIPTION_LENGTH})",
        title="Security: Input Too Long"
    )
    raise SystemExit(1)
```

### Path Traversal Prevention

Prevent path traversal attacks when handling file paths:

```python
from pathlib import Path
from github_action_toolkit import get_user_input, error

def get_safe_file_path(base_dir: Path) -> Path:
    """Get validated file path within base directory."""
    file_path = get_user_input('file-path')
    if not file_path:
        raise ValueError("file-path is required")
    
    # Resolve to absolute path
    requested_path = (base_dir / file_path).resolve()
    
    # Ensure it's within base directory
    if not requested_path.is_relative_to(base_dir):
        error(
            f"Invalid file path: {file_path}. "
            "Path must be within the workspace.",
            title="Security: Path Traversal Attempt"
        )
        raise SystemExit(1)
    
    return requested_path
```

## Secrets Management

### Masking Secrets

Always mask secrets in logs:

```python
from github_action_toolkit import add_mask, info

# Mask before any use
api_key = get_secret('api_key')
add_mask(api_key)

# Now safe to log
info(f"Using API key: {api_key}")  # Will appear as "***"
```

### Derived Secrets

Mask any values derived from secrets:

```python
from github_action_toolkit import add_mask
import hashlib

api_key = get_secret('api_key')
add_mask(api_key)

# Hash or transform
key_hash = hashlib.sha256(api_key.encode()).hexdigest()
add_mask(key_hash)  # Mask derived values too!

# Concatenations
combined = f"Bearer {api_key}"
add_mask(combined)
```

### Never Log Secrets

```python
# ❌ NEVER DO THIS
api_key = get_secret('api_key')
print(f"API Key: {api_key}")  # Exposed in logs!

# ✅ DO THIS
api_key = get_secret('api_key')
add_mask(api_key)
info("API key configured successfully")  # Safe
```

### Temporary Files with Secrets

Clean up temporary files containing secrets:

```python
from pathlib import Path
from github_action_toolkit import add_mask
import os

def use_secret_file(secret: str):
    """Safely use secret in a temporary file."""
    add_mask(secret)
    
    temp_file = Path('/tmp/secret.txt')
    try:
        # Use restrictive permissions (owner read/write only)
        temp_file.write_text(secret)
        temp_file.chmod(0o600)
        
        # Use the file
        process_secret_file(temp_file)
    finally:
        # Always clean up
        if temp_file.exists():
            temp_file.unlink()
```

## Dependency Security

### Pin Versions

Always pin dependency versions in your action:

```yaml
# ❌ Unpinned - risky
runs:
  using: 'composite'
  steps:
    - run: pip install github-action-toolkit
      shell: bash

# ✅ Pinned - safer
runs:
  using: 'composite'
  steps:
    - run: pip install github-action-toolkit==0.7.0
      shell: bash
```

### Verify Checksums

For critical dependencies, verify checksums:

```python
import hashlib
from pathlib import Path

def verify_file_checksum(file_path: Path, expected_hash: str):
    """Verify file integrity with SHA-256."""
    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b''):
            sha256_hash.update(byte_block)
    
    actual_hash = sha256_hash.hexdigest()
    if actual_hash != expected_hash:
        raise SecurityError(
            f"Checksum mismatch for {file_path}!\n"
            f"Expected: {expected_hash}\n"
            f"Actual: {actual_hash}"
        )
```

### Scan Dependencies

Use tools to scan for known vulnerabilities:

```yaml
# In your workflow
- name: Scan dependencies
  run: |
    pip install safety
    safety check --json
```

## Code Injection Prevention

### Command Injection

Never use user input directly in shell commands:

```python
from github_action_toolkit import get_user_input
import subprocess
import shlex

# ❌ DANGEROUS - Command injection risk
branch = get_user_input('branch')
subprocess.run(f"git checkout {branch}", shell=True)  # NEVER DO THIS!

# ✅ SAFE - Use list and avoid shell
branch = get_user_input('branch')
subprocess.run(['git', 'checkout', branch], shell=False, check=True)

# ✅ SAFE - Quote if shell=True is absolutely needed
branch = get_user_input('branch')
quoted_branch = shlex.quote(branch)
subprocess.run(f"git checkout {quoted_branch}", shell=True, check=True)
```

### SQL Injection Prevention

Use parameterized queries:

```python
import sqlite3

# ❌ DANGEROUS
user_input = get_user_input('username')
cursor.execute(f"SELECT * FROM users WHERE username = '{user_input}'")

# ✅ SAFE - Use parameters
user_input = get_user_input('username')
cursor.execute("SELECT * FROM users WHERE username = ?", (user_input,))
```

### Template Injection

Be careful with user input in templates:

```python
from github_action_toolkit import get_user_input
from string import Template

# ❌ DANGEROUS - f-string with user input
name = get_user_input('name')
message = f"Hello {name}"  # Could be "Hello ${SECRET}"

# ✅ SAFER - Use Template with safe substitution
template = Template("Hello $name")
message = template.safe_substitute(name=name)
```

## API Token Security

### Minimal Permissions

Request only the permissions you need:

```yaml
# In your workflow
permissions:
  contents: read      # Only what's needed
  pull-requests: write # No more than necessary
```

### Token Scoping

Use scoped tokens when possible:

```python
from github_action_toolkit import GitHubAPIClient

# Use installation token with scoped permissions
client = GitHubAPIClient(
    github_token=get_installation_token(),  # Scoped token
)

# Not personal access token with full access
```

### Token Expiry

For long-running operations, handle token expiry:

```python
from github_action_toolkit import GitHubAPIClient, warning
import time

def operation_with_token_refresh():
    """Handle token expiry in long operations."""
    client = GitHubAPIClient()
    start_time = time.time()
    
    for item in large_dataset:
        # Refresh token every hour (GitHub tokens last ~1 hour)
        if time.time() - start_time > 3000:  # 50 minutes
            warning("Token may expire soon, consider refreshing")
            # Refresh logic here
            start_time = time.time()
        
        process_item(client, item)
```

## Environment Variable Safety

### Avoid Exporting Secrets

Never export secrets as environment variables unless absolutely necessary:

```python
from github_action_toolkit import add_mask
import os

# ❌ RISKY - Exported to environment
api_key = get_secret('api_key')
os.environ['API_KEY'] = api_key  # Now visible to all subprocesses

# ✅ BETTER - Pass directly as needed
api_key = get_secret('api_key')
add_mask(api_key)
make_api_call(api_key=api_key)
```

### Clean Environment

Remove secrets from environment after use:

```python
from github_action_toolkit import with_env

# Automatically cleaned up
with with_env(TEMP_SECRET=secret_value):
    # Use secret here
    pass
# Secret removed from environment here
```

## Artifact Security

### Validate Artifact Contents

Don't trust artifact contents without validation:

```python
from github_action_toolkit import GitHubArtifacts
from pathlib import Path
import zipfile

def safe_extract_artifact(artifact_id: int, dest: Path):
    """Safely extract artifact with validation."""
    artifacts = GitHubArtifacts()
    
    # Download to temp location
    temp_zip = Path('/tmp/artifact.zip')
    artifacts.download_artifact(artifact_id, str(temp_zip))
    
    # Validate before extracting
    with zipfile.ZipFile(temp_zip, 'r') as zf:
        # Check for path traversal in zip
        for name in zf.namelist():
            if name.startswith('/') or '..' in name:
                raise SecurityError(
                    f"Malicious path in artifact: {name}"
                )
        
        # Check compressed size
        total_size = sum(info.file_size for info in zf.infolist())
        if total_size > 100 * 1024 * 1024:  # 100 MB
            raise SecurityError("Artifact too large")
        
        # Safe to extract
        zf.extractall(dest)
```

### Artifact Retention

Don't keep sensitive artifacts forever:

```python
from github_action_toolkit import GitHubArtifacts

artifacts = GitHubArtifacts()

# Set short retention for sensitive data
artifacts.upload_artifact(
    name='sensitive-logs',
    paths=['logs/'],
    retention_days=1  # Delete after 1 day
)
```

## Network Security

### HTTPS Only

Always use HTTPS for external requests:

```python
import requests

def safe_api_call(url: str):
    """Make API call with security checks."""
    # Ensure HTTPS
    if not url.startswith('https://'):
        raise SecurityError(
            f"Only HTTPS URLs allowed, got: {url}"
        )
    
    response = requests.get(
        url,
        timeout=30,  # Prevent hanging
        verify=True,  # Verify SSL certificates
    )
    return response
```

### Verify SSL Certificates

Never disable certificate verification in production:

```python
import requests

# ❌ NEVER DO THIS IN PRODUCTION
response = requests.get(url, verify=False)

# ✅ Always verify certificates
response = requests.get(url, verify=True)
```

### Rate Limiting

Implement rate limiting for external calls:

```python
import time
from collections import deque

class RateLimiter:
    """Simple rate limiter."""
    
    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls
        self.period = period
        self.calls = deque()
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        now = time.time()
        
        # Remove old calls
        while self.calls and self.calls[0] < now - self.period:
            self.calls.popleft()
        
        # Wait if at limit
        if len(self.calls) >= self.max_calls:
            sleep_time = self.period - (now - self.calls[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        self.calls.append(now)

# Use it
limiter = RateLimiter(max_calls=10, period=60)  # 10 calls per minute
for url in urls:
    limiter.wait_if_needed()
    fetch(url)
```

## Security Checklist

Use this checklist when reviewing your action:

### Input Handling
- [ ] All inputs validated and sanitized
- [ ] Input length limits enforced
- [ ] Path traversal prevented
- [ ] Command injection prevented
- [ ] SQL injection prevented (if using DB)

### Secrets Management
- [ ] All secrets masked with `add_mask()`
- [ ] Secrets never logged or printed
- [ ] Derived values from secrets are masked
- [ ] Temporary files with secrets cleaned up
- [ ] Secrets not exported to environment unnecessarily

### Dependencies
- [ ] All dependency versions pinned
- [ ] Known vulnerabilities checked
- [ ] Minimal dependencies used
- [ ] Dependencies from trusted sources only

### API Security
- [ ] Minimal token permissions requested
- [ ] Token expiry handled
- [ ] Rate limits respected
- [ ] HTTPS enforced
- [ ] SSL certificates verified

### Artifacts
- [ ] Artifact contents validated before use
- [ ] Sensitive artifacts have short retention
- [ ] No secrets in artifact names or metadata

### Code Quality
- [ ] No hardcoded secrets
- [ ] Error messages don't expose sensitive info
- [ ] Logging doesn't expose sensitive data
- [ ] File permissions restrictive for sensitive files

## Reporting Security Issues

If you discover a security vulnerability in github-action-toolkit:

1. **DO NOT** open a public issue
2. Email security concerns to the maintainers
3. Include a detailed description and reproduction steps
4. Allow time for a fix before public disclosure

See [SECURITY.md](https://github.com/VatsalJagani/github-action-toolkit-python/blob/main/SECURITY.md) for more details.

## Additional Resources

- [GitHub Actions Security Best Practices](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)

