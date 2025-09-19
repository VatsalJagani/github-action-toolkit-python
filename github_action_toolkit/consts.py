import os

COMMAND_MARKER: str = "::"
COMMANDS_USE_SUBPROCESS: bool = bool(os.environ.get("COMMANDS_USE_SUBPROCESS", False))
