"""
Constants used throughout the github-action-toolkit.

These constants control command formatting, subprocess usage, and environment
variable delimiters for GitHub Actions workflows.
"""

import os

# Marker used to format GitHub Actions workflow commands
COMMAND_MARKER: str = "::"

# Whether to use subprocess for executing commands instead of direct output
COMMANDS_USE_SUBPROCESS: bool = bool(os.environ.get("COMMANDS_USE_SUBPROCESS", False))

# Delimiter used for multi-line environment variables in heredoc format
ACTION_ENV_DELIMITER: str = "__ENV_DELIMITER__"
