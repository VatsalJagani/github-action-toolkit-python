GitHub Cache Functions
================

### **`GitHubCache(github_token=None, github_repo=None)` Class**

Initializes the cache client for GitHub Actions cache operations. Enables performance optimizations through caching across workflow runs, supporting hierarchical key fallbacks and cross-job data sharing.

Both parameters are optional but environment variables for them need to be present: GITHUB_TOKEN and GITHUB_REPOSITORY respectively.

**example:**

```python
>> from github_action_toolkit import GitHubCache
>> cache = GitHubCache()
```

### **`GitHubCache.save_cache(paths, key, enable_cross_os_archive=False)`**

Save cache with the specified key. Supports composite keys for fine-grained cache management.

* `paths`: List of file/directory paths to cache (list of strings or Path objects)
* `key`: Primary cache key (can include variables like version, hash, platform)
* `enable_cross_os_archive` (optional): Enable cross-OS compatibility (default: False)

Returns the cache ID if successful, None if cache already exists.

**example:**

```python
>> import hashlib
>> from pathlib import Path
>>
>> # Calculate hash of lockfile for cache key
>> lockfile = Path("package-lock.json")
>> lockfile_hash = hashlib.sha256(lockfile.read_bytes()).hexdigest()[:8]
>>
>> # Create composite key with platform and hash
>> import platform
>> cache_key = f"npm-{platform.system()}-{lockfile_hash}"
>>
>> # Save node_modules to cache
>> paths = ["node_modules", ".npm"]
>> cache_id = cache.save_cache(paths, cache_key)
>> if cache_id:
>>     print(f"Cache saved with ID: {cache_id}")
>> else:
>>     print("Cache already exists")

# Output:
# Cache saved with ID: 123456
```

### **`GitHubCache.restore_cache(paths, primary_key, restore_keys=None, enable_cross_os_archive=False)`**

Restore cache with fallback key hierarchy. Tries the primary key first, then falls back to restore keys in order.

* `paths`: List of file/directory paths to restore to (list of strings or Path objects)
* `primary_key`: Primary cache key to look for (exact match)
* `restore_keys` (optional): List of fallback keys to try if primary not found (supports prefix matching)
* `enable_cross_os_archive` (optional): Enable cross-OS compatibility (default: False)

Returns the matched cache key if found and restored, None if no cache found.

**example:**

```python
>> import hashlib
>> import platform
>> from pathlib import Path
>>
>> # Calculate hash for primary key
>> lockfile_hash = hashlib.sha256(Path("package-lock.json").read_bytes()).hexdigest()[:8]
>> system = platform.system()
>>
>> # Define primary and fallback keys
>> primary_key = f"npm-{system}-{lockfile_hash}"
>> restore_keys = [
>>     f"npm-{system}-",  # Any cache for this OS
>>     "npm-",            # Any npm cache
>> ]
>>
>> # Try to restore cache
>> matched_key = cache.restore_cache(["node_modules"], primary_key, restore_keys)
>> if matched_key:
>>     print(f"Cache restored from key: {matched_key}")
>> else:
>>     print("No cache found")

# Output:
# Cache restored from key: npm-Linux-abc12345
```

### **`GitHubCache.is_feature_available()`**

Check if the cache feature is available in the current environment. Useful for gracefully handling cases where cache is not available.

Returns True if cache is available, False otherwise.

**example:**

```python
>> if cache.is_feature_available():
>>     print("Cache is available")
>>     cache.save_cache(paths, key)
>> else:
>>     print("Cache is not available, skipping")

# Output:
# Cache is available
```

## Common Usage Patterns

### Caching Dependencies

```python
from github_action_toolkit import GitHubCache
import hashlib
import platform
from pathlib import Path

cache = GitHubCache()

# Generate cache key from lockfile
lockfile = Path("requirements.txt")
lockfile_hash = hashlib.sha256(lockfile.read_bytes()).hexdigest()[:8]
cache_key = f"python-{platform.system()}-{lockfile_hash}"

# Try to restore cache
restore_keys = [f"python-{platform.system()}-"]
matched_key = cache.restore_cache([".venv"], cache_key, restore_keys)

if matched_key:
    print(f"Dependencies restored from cache: {matched_key}")
else:
    print("No cache found, installing dependencies...")
    # Install dependencies here
    
    # Save to cache for next time
    cache_id = cache.save_cache([".venv"], cache_key)
    if cache_id:
        print(f"Dependencies cached with ID: {cache_id}")
```

### Cross-Job Data Passing

```python
# Job 1: Build and cache artifacts
from github_action_toolkit import GitHubCache

cache = GitHubCache()
build_key = f"build-{os.environ['GITHUB_SHA']}"

# Build your project
# ... build process ...

# Cache build outputs
cache.save_cache(["dist", "build"], build_key)

# Job 2: Use cached artifacts
from github_action_toolkit import GitHubCache

cache = GitHubCache()
build_key = f"build-{os.environ['GITHUB_SHA']}"

# Restore build outputs from Job 1
matched_key = cache.restore_cache(["dist", "build"], build_key)
if matched_key:
    print("Build artifacts restored")
    # Use artifacts for deployment/testing
```

## Exception Handling

The cache module provides specific exceptions for different error scenarios:

```python
from github_action_toolkit import (
    GitHubCache,
    CacheNotFoundError,
    CacheRestoreError,
    CacheSaveError
)

cache = GitHubCache()

try:
    cache.save_cache(["node_modules"], "my-cache-key")
except CacheSaveError as e:
    print(f"Failed to save cache: {e}")

try:
    cache.restore_cache(["node_modules"], "my-cache-key")
except CacheRestoreError as e:
    print(f"Failed to restore cache: {e}")
```

## Cache Key Best Practices

1. **Include platform information** for OS-specific dependencies:
   ```python
   key = f"deps-{platform.system()}-{hash}"
   ```

2. **Use file hashes** for exact dependency matching:
   ```python
   hash = hashlib.sha256(Path("package-lock.json").read_bytes()).hexdigest()[:8]
   ```

3. **Create fallback hierarchy** for better cache hit rates:
   ```python
   primary = f"npm-Linux-abc12345"
   fallbacks = ["npm-Linux-", "npm-"]
   ```

4. **Keep keys under 512 characters** to comply with GitHub's limits.

5. **Use semantic versioning** in keys when appropriate:
   ```python
   key = f"build-v1.2.3-{platform.system()}"
   ```
