from __future__ import annotations

import os
import threading
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from warnings import warn

from .consts import ACTION_ENV_DELIMITER
from .exceptions import EnvironmentVariableError, InputError
from .print_messages import echo, escape_data, escape_property, group

# Thread-local lock for file operations to ensure thread-safety
_file_locks: dict[str, threading.Lock] = {}
_locks_lock = threading.Lock()


def _get_file_lock(filepath: str) -> threading.Lock:
    """Get or create a lock for a specific file path."""
    with _locks_lock:
        if filepath not in _file_locks:
            _file_locks[filepath] = threading.Lock()
        return _file_locks[filepath]


def _write_to_file(filepath: str, content: bytes) -> None:
    """
    Thread-safe atomic write to a file.

    :param filepath: Path to the file
    :param content: Content to write (as bytes)
    :raises: IOError if file cannot be written
    """
    lock = _get_file_lock(filepath)
    with lock:
        try:
            with open(filepath, "ab") as f:
                f.write(content)
                f.flush()  # Ensure data is written to disk
                os.fsync(f.fileno())  # Force write to disk for atomicity
        except OSError as e:
            raise OSError(f"Failed to write to {filepath}: {e}") from e


def _build_file_input(name: str, value: Any) -> bytes:
    """
    Build properly formatted and escaped environment file input.

    Uses heredoc-style delimiters to safely handle multi-line values.
    Validates that the delimiter doesn't appear in the value to prevent injection.

    :param name: Variable name
    :param value: Variable value
    :returns: Properly formatted bytes for writing to env file
    :raises ValueError: If the delimiter appears in the value (extremely rare)
    """
    escaped_value = escape_data(value)

    # Validate that our delimiter doesn't appear in the escaped value
    # This is extremely unlikely but we check for safety
    if ACTION_ENV_DELIMITER in escaped_value:
        raise ValueError(
            f"Value contains the delimiter '{ACTION_ENV_DELIMITER}'. "
            "This is not supported for security reasons."
        )

    return (
        f"{escape_property(name)}"
        f"<<{ACTION_ENV_DELIMITER}\n"
        f"{escaped_value}\n"
        f"{ACTION_ENV_DELIMITER}\n".encode()
    )


def get_all_user_inputs() -> dict[str, str]:
    """
    Retrieves all environment variables that start with 'INPUT_'.

    :returns: Dictionary of input names and their values.
    """
    return {key[6:].lower(): value for key, value in os.environ.items() if key.startswith("INPUT_")}


def print_all_user_inputs() -> None:
    """
    Prints all user inputs (from environment variables) to the console.
    """
    inputs = get_all_user_inputs()
    if not inputs:
        echo("No user inputs found.")
        return

    with group("User Inputs:"):
        for name, value in inputs.items():
            echo(f"  {name}: {value}")


def get_user_input(name: str) -> str | None:
    """
    gets user input from environment variables.

    :param name: Name of the user input
    :returns: input value or None
    """
    return os.environ.get(f"INPUT_{name.upper()}")


def get_user_input_as(name: str, input_type: type, default_value: Any = None) -> Any:
    """
    gets user input from environment variables and casts it to the specified type.

    :param name: Name of the user input
    :param input_type: Type to cast the input value to (e.g., str, int, float, bool)
    :param default_value: In case the input is not provided return this as default value (e.g., True, False, 0, etc)
    :returns: input value cast to the specified type or None
    :raises InputError: When the input value cannot be converted to the specified type
    """
    value = get_user_input(name)
    if value is None:
        return default_value

    try:
        if input_type is bool:
            if default_value is True:
                if value in ("false", "f", "0", "n", "no"):
                    return False
                else:
                    return True
            elif default_value is False:
                if value in ("true", "t", "1", "y", "yes"):
                    return True
                else:
                    return False
            else:
                return input_type(value)

        else:
            if value == "":
                return default_value
            else:
                return input_type(value)

    except ValueError as e:
        raise InputError(
            f"Cannot convert input '{name}' with value '{value}' to {input_type.__name__}. "
            f"Provide a valid {input_type.__name__} value for input '{name}'."
        ) from e


def set_output(name: str, value: Any, use_subprocess: bool | None = None) -> None:
    """
    sets out for your workflow using GITHUB_OUTPUT file.

    :param name: name of the output
    :param value: value of the output
    :returns: None
    :raises EnvironmentVariableError: When GITHUB_OUTPUT environment variable is not set
    """
    if use_subprocess is not None:
        warn(
            "Argument `use_subprocess` for `set_output()` is deprecated and "
            "going to be removed in the next version.",
            DeprecationWarning,
            stacklevel=2,
        )

    output_file = os.environ.get("GITHUB_OUTPUT")
    if not output_file:
        raise EnvironmentVariableError(
            "GITHUB_OUTPUT environment variable is not set. "
            "This function must be run in a GitHub Actions context."
        )

    _write_to_file(output_file, _build_file_input(name, value))


def get_state(name: str) -> str | None:
    """
    gets environment variable value for the state.

    :param name: Name of the state environment variable (e.g: STATE_{name})
    :returns: state value or None
    """
    return os.environ.get(f"STATE_{name}")


def save_state(name: str, value: Any, use_subprocess: bool | None = None) -> None:
    """
    sets state for your workflow using $GITHUB_STATE file
    for sharing it with your workflow's pre: or post: actions.

    :param name: Name of the state environment variable (e.g: STATE_{name})
    :param value: value of the state environment variable
    :returns: None
    :raises EnvironmentVariableError: When GITHUB_STATE environment variable is not set
    """
    if use_subprocess is not None:
        warn(
            "Argument `use_subprocess` for `save_state()` is deprecated and "
            "going to be removed in the next version.",
            DeprecationWarning,
            stacklevel=2,
        )

    state_file = os.environ.get("GITHUB_STATE")
    if not state_file:
        raise EnvironmentVariableError(
            "GITHUB_STATE environment variable is not set. "
            "This function must be run in a GitHub Actions context."
        )

    _write_to_file(state_file, _build_file_input(name, value))


def get_workflow_environment_variables() -> dict[str, Any]:
    """
    get a dictionary of all environment variables set in the GitHub Actions workflow.

    :returns: dictionary of all environment variables
    :raises EnvironmentVariableError: When GITHUB_ENV environment variable is not set
    """
    env_file = os.environ.get("GITHUB_ENV")
    if not env_file:
        raise EnvironmentVariableError(
            "GITHUB_ENV environment variable is not set. "
            "This function must be run in a GitHub Actions context."
        )

    environment_variable_dict: dict[str, str] = {}
    marker = f"<<{ACTION_ENV_DELIMITER}"

    with open(env_file, "rb") as file:
        for line in file:
            decoded_line: str = line.decode("utf-8")

            if marker in decoded_line:
                name, *_ = decoded_line.strip().split("<<")

                try:
                    decoded_value = next(file).decode("utf-8").strip()
                    environment_variable_dict[name] = decoded_value  # ← move inside try
                except StopIteration:
                    break

    return environment_variable_dict


def get_env(name: str) -> Any:
    """
    gets the value of an environment variable set in the GitHub Actions workflow.

    :param name: name of the environment variable
    :returns: value of the environment variable or None
    """
    return os.environ.get(name) or get_workflow_environment_variables().get(name)


def set_env(name: str, value: Any) -> None:
    """
    sets an environment variable for your workflows $GITHUB_ENV file.

    :param name: name of the environment variable
    :param value: value of the environment variable
    :returns: None
    :raises EnvironmentVariableError: When GITHUB_ENV environment variable is not set
    """
    env_file = os.environ.get("GITHUB_ENV")
    if not env_file:
        raise EnvironmentVariableError(
            "GITHUB_ENV environment variable is not set. "
            "This function must be run in a GitHub Actions context."
        )

    with open(env_file, "ab") as f:
        f.write(_build_file_input(name, value))


@contextmanager
def with_env(**env_vars: str) -> Generator[None, None, None]:
    """
    Temporarily set environment variables within a context.

    Environment variables are restored to their original values (or removed if they
    didn't exist) when the context exits.

    Example:
        with with_env(MY_VAR="value", ANOTHER="test"):
            # MY_VAR and ANOTHER are set here
            pass
        # Variables are restored here

    :param env_vars: Environment variables to set as keyword arguments
    :returns: Context manager that handles environment variable scoping
    """
    original_values: dict[str, str | None] = {}

    for key in env_vars:
        original_values[key] = os.environ.get(key)

    try:
        for key, value in env_vars.items():
            os.environ[key] = value
        yield
    finally:
        for key, original_value in original_values.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


def export_variable(name: str, value: Any) -> None:
    """
    Sets an environment variable for your workflows (alias for set_env).
    This matches the naming convention from the Javascript actions/toolkit.

    :param name: name of the environment variable
    :param value: value of the environment variable
    :returns: None
    """
    set_env(name, value)


def add_path(path: str | Path) -> None:
    """
    Prepends a directory to the system PATH for all subsequent actions in the current job.
    The newly added path is available in the current action and all subsequent actions.

    :param path: Absolute path to add to PATH
    :returns: None
    """
    path_str = str(path) if isinstance(path, Path) else path

    # Validate that the path is absolute
    if not os.path.isabs(path_str):
        raise ValueError(f"Path '{path_str}' must be an absolute path")

    # Write to GITHUB_PATH file
    _write_to_file(os.environ["GITHUB_PATH"], f"{path_str}\n".encode())
