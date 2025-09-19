import os
from typing import Any, Dict, Union
from warnings import warn

from .consts import ACTION_ENV_DELIMITER
from .print_messages import _escape_data, _escape_property


def _build_file_input(name: str, value: Any) -> bytes:
    return (
        f"{_escape_property(name)}"
        f"<<{ACTION_ENV_DELIMITER}\n"
        f"{_escape_data(value)}\n"
        f"{ACTION_ENV_DELIMITER}\n".encode("utf-8")
    )


def get_user_input(name: str) -> Union[str, None]:
    """
    gets user input from environment variables.

    :param name: Name of the user input
    :returns: input value or None
    """
    return os.environ.get(f"INPUT_{name.upper()}")


def set_output(name: str, value: Any, use_subprocess: Union[bool, None] = None) -> None:
    """
    sets out for your workflow using GITHUB_OUTPUT file.

    :param name: name of the output
    :param value: value of the output
    :returns: None
    """
    if use_subprocess is not None:
        warn(
            "Argument `use_subprocess` for `set_output()` is deprecated and "
            "going to be removed in the next version.",
            DeprecationWarning,
        )

    with open(os.environ["GITHUB_OUTPUT"], "ab") as f:
        f.write(_build_file_input(name, value))


def get_state(name: str) -> Union[str, None]:
    """
    gets environment variable value for the state.

    :param name: Name of the state environment variable (e.g: STATE_{name})
    :returns: state value or None
    """
    return os.environ.get(f"STATE_{name}")


def save_state(name: str, value: Any, use_subprocess: Union[bool, None] = None) -> None:
    """
    sets state for your workflow using $GITHUB_STATE file
    for sharing it with your workflow's pre: or post: actions.

    :param name: Name of the state environment variable (e.g: STATE_{name})
    :param value: value of the state environment variable
    :returns: None
    """
    if use_subprocess is not None:
        warn(
            "Argument `use_subprocess` for `save_state()` is deprecated and "
            "going to be removed in the next version.",
            DeprecationWarning,
        )

    with open(os.environ["GITHUB_STATE"], "ab") as f:
        f.write(_build_file_input(name, value))


def get_workflow_environment_variables() -> Dict[str, Any]:
    """
    get a dictionary of all environment variables set in the GitHub Actions workflow.

    :returns: dictionary of all environment variables
    """
    environment_variable_dict = {}
    marker = f"<<{ACTION_ENV_DELIMITER}"

    with open(os.environ["GITHUB_ENV"], "rb") as file:
        for line in file:
            decoded_line: str = line.decode("utf-8")

            if marker in decoded_line:
                name, *_ = decoded_line.strip().split("<<")

                try:
                    decoded_value = next(file).decode("utf-8").strip()
                except StopIteration:
                    break
            environment_variable_dict[name] = decoded_value
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
    """
    with open(os.environ["GITHUB_ENV"], "ab") as f:
        f.write(_build_file_input(name, value))
