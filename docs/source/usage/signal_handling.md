# Signal Handling & Cancellation

Handle workflow cancellation and SIGTERM/SIGINT signals gracefully.

## Overview

The `CancellationHandler` class provides unified handling for managing cancellation signals in GitHub Actions workflows, allowing you to clean up resources and exit gracefully when a workflow is cancelled.

## API Reference

### `CancellationHandler()`

Creates a new cancellation handler instance.

**Example:**

```python
from github_action_toolkit import CancellationHandler

handler = CancellationHandler()
```

### `enable()`

Enable automatic handling of cancellation signals (SIGTERM and SIGINT). When enabled, cancellation signals will:
1. Call all registered cancellation handlers
2. Raise a `CancellationRequested` exception

**example:**

```python
from github_action_toolkit import CancellationHandler
from github_action_toolkit.exceptions import CancellationRequested

handler = CancellationHandler()
handler.enable()

try:
    # Your long-running operation
    process_data()
except CancellationRequested:
    print("Operation was cancelled, cleaning up...")
finally:
    handler.disable()
```

### `disable()`

Disable automatic handling of cancellation signals and restore original signal handlers.

**example:**

```python
from github_action_toolkit import CancellationHandler

handler = CancellationHandler()
handler.enable()
# ... do work ...
handler.disable()
```

### `is_enabled()`

Check if cancellation support is currently enabled for this handler.

**example:**

```python
from github_action_toolkit import CancellationHandler

handler = CancellationHandler()
if handler.is_enabled():
    print("Cancellation support is active")
```

### `register(handler_func)`

Register a cleanup handler to be called when cancellation is requested. Handlers are called in the order they were registered.

**example:**

```python
from github_action_toolkit import CancellationHandler

def cleanup_database():
    print("Closing database connections...")
    # Cleanup code

def cleanup_files():
    print("Removing temporary files...")
    # Cleanup code

cancellation = CancellationHandler()
cancellation.register(cleanup_database)
cancellation.register(cleanup_files)
cancellation.enable()

# Both handlers will be called on cancellation
```

## CancellationRequested Exception

Exception raised when a cancellation signal (SIGTERM or SIGINT) is received. Catch this exception to handle cancellation gracefully.

Import from `github_action_toolkit.exceptions`:

```python
from github_action_toolkit.exceptions import CancellationRequested
```

**example:**

```python
from github_action_toolkit import CancellationRequested, enable_cancellation_support
import time

enable_cancellation_support()

try:
    for i in range(100):
        print(f"Processing item {i}...")
        time.sleep(1)
except CancellationRequested as e:
    print(f"Cancelled: {e}")
    # Perform cleanup
    save_progress(i)
```

## Complete Example

Here's a complete example showing how to use cancellation support in a GitHub Action:

```python
from github_action_toolkit import (
    enable_cancellation_support,
    register_cancellation_handler,
    CancellationRequested,
    info,
    warning,
)
import time

# Track progress
progress_file = "/tmp/progress.txt"

def save_progress(current_item):
    """Save current progress for resumption"""
    with open(progress_file, "w") as f:
        f.write(str(current_item))
    info(f"Progress saved: {current_item}")

def cleanup():
    """Cleanup handler called on cancellation"""
    warning("Cleaning up resources...")
    # Close connections, save state, etc.

# Set up cancellation support
register_cancellation_handler(cleanup)
enable_cancellation_support()

try:
    info("Starting long-running operation...")
    
    # Your main workflow logic
    for i in range(1000):
        info(f"Processing item {i}")
        time.sleep(0.1)
        
        # Periodically save progress
        if i % 100 == 0:
            save_progress(i)
    
    info("Operation completed successfully")
    
except CancellationRequested as e:
    warning(f"Operation cancelled: {e}")
    # Save final progress before exit
    save_progress(i)
    exit(1)
    
except Exception as e:
    error(f"Operation failed: {e}")
    exit(1)
```

## Best Practices

### Always Enable Early

Enable cancellation support at the start of your action, before any long-running operations:

```python
enable_cancellation_support()
# Rest of your code
```

### Register Cleanup Handlers

Register handlers for any resources that need cleanup:

```python
register_cancellation_handler(close_database_connections)
register_cancellation_handler(remove_temp_files)
register_cancellation_handler(stop_background_processes)
```

### Save Progress

For long-running operations, periodically save progress so work can be resumed:

```python
try:
    for item in large_dataset:
        process(item)
        if should_save_checkpoint():
            save_progress()
except CancellationRequested:
    save_progress()  # Final save before exit
```

### Handle Exceptions in Handlers

Cancellation handlers should be defensive and catch their own exceptions:

```python
def cleanup_handler():
    try:
        close_connections()
    except Exception as e:
        print(f"Error during cleanup: {e}")
        # Continue with other cleanup
```

### Don't Block in Handlers

Keep cancellation handlers fast. Avoid long-running operations that would delay shutdown:

```python
def quick_cleanup():
    # Good: Fast cleanup
    close_file_handles()
    
def slow_cleanup():
    # Bad: Blocks shutdown
    for i in range(1000):
        process_item(i)
```
