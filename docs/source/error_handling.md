Error Handling
================

## Graceful Degradation

```python
from github_action_toolkit import warning, info, error

def process_with_fallback():
    """Try primary method, fall back to secondary."""
    try:
        result = primary_method()
        info('Used primary method successfully')
        return result
    except Exception as e:
        warning(
            f'Primary method failed: {e}. Trying fallback method.',
            title='Fallback Activated'
        )
        try:
            result = fallback_method()
            info('Fallback method succeeded')
            return result
        except Exception as e2:
            error(f'Both methods failed: {e2}', title='Processing Failed')
            raise
```

## Retry with Backoff

```python
import time
from github_action_toolkit import info, warning

def retry_with_backoff(func, max_attempts=3, base_delay=1):
    """Retry a function with exponential backoff."""
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            
            delay = base_delay * (2 ** attempt)
            warning(
                f'Attempt {attempt + 1} failed: {e}. '
                f'Retrying in {delay}s...',
                title='Retry'
            )
            time.sleep(delay)
```

## Context Information in Errors

```python
from github_action_toolkit import error
from github_action_toolkit.exceptions import GitHubActionError

class ProcessingError(GitHubActionError):
    """Error with context about what was being processed."""
    
    def __init__(self, message: str, file: str, line: int | None = None):
        self.file = file
        self.line = line
        super().__init__(
            f"{message} (in {file}" + 
            (f", line {line}" if line else "") + ")"
        )

# Usage
try:
    process_file('data.json')
except Exception as e:
    raise ProcessingError(
        f"Failed to parse JSON: {e}",
        file='data.json',
        line=42
    )
```
