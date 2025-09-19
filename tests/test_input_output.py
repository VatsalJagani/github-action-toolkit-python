import os
from typing import Any
from unittest import mock

import pytest

import github_action_toolkit as gat
import github_action_toolkit.input_output as gha_utils_input_output


def test__build_file_input() -> None:
    assert (
        gha_utils_input_output._build_file_input("test", "value")
        == b"test<<__ENV_DELIMITER__\nvalue\n__ENV_DELIMITER__\n"
    )


def test_set_output(tmpdir: Any) -> None:
    file = tmpdir.join("output_file")

    with mock.patch.dict(os.environ, {"GITHUB_OUTPUT": file.strpath}):
        gat.set_output("test", "test")
        gat.set_output("another", 2)

    assert file.read() == (
        "test<<__ENV_DELIMITER__\n"
        "test\n__ENV_DELIMITER__\n"
        "another<<__ENV_DELIMITER__\n2\n"
        "__ENV_DELIMITER__\n"
    )


def test_set_output_deprecation_warning(tmpdir: Any) -> None:
    file = tmpdir.join("output_file")

    with pytest.deprecated_call():
        with mock.patch.dict(os.environ, {"GITHUB_OUTPUT": file.strpath}):
            gat.set_output("test", "test", use_subprocess=True)


def test_save_state(tmpdir: Any) -> None:
    file = tmpdir.join("state_file")

    with mock.patch.dict(os.environ, {"GITHUB_STATE": file.strpath}):
        gat.save_state("test", "test")
        gat.save_state("another", 2)

    assert file.read() == (
        "test<<__ENV_DELIMITER__\n"
        "test\n__ENV_DELIMITER__\n"
        "another<<__ENV_DELIMITER__\n2\n"
        "__ENV_DELIMITER__\n"
    )


def test_save_state_deprecation_warning(tmpdir: Any) -> None:
    file = tmpdir.join("state_file")

    with pytest.deprecated_call():
        with mock.patch.dict(os.environ, {"GITHUB_STATE": file.strpath}):
            gat.save_state("test", "test", use_subprocess=True)


@mock.patch.dict(os.environ, {"STATE_test_state": "test", "abc": "another test"})
def test_get_state() -> None:
    assert gat.get_state("test_state") == "test"
    assert gat.get_state("abc") is None


@mock.patch.dict(os.environ, {"INPUT_USERNAME": "test", "ANOTHER": "another test"})
def test_get_user_input() -> None:
    assert gat.get_user_input("username") == "test"
    assert gat.get_user_input("another") is None


def test_set_env(tmpdir: Any) -> None:
    file = tmpdir.join("envfile")

    with mock.patch.dict(os.environ, {"GITHUB_ENV": file.strpath}):
        gat.set_env("test", "test")
        gat.set_env("another", 2)

    assert file.read() == (
        "test<<__ENV_DELIMITER__\n"
        "test\n__ENV_DELIMITER__\n"
        "another<<__ENV_DELIMITER__\n2\n"
        "__ENV_DELIMITER__\n"
    )


def test_get_workflow_environment_variables(tmpdir: Any) -> None:
    file = tmpdir.join("envfile")

    with mock.patch.dict(os.environ, {"GITHUB_ENV": file.strpath}):
        gat.set_env("test", "test")
        gat.set_env("another", 2)
        data = gat.get_workflow_environment_variables()

    assert data == {"test": "test", "another": "2"}


@mock.patch.dict(os.environ, {"GITHUB_ACTOR": "test", "ANOTHER": "another test"})
def test_get_env() -> None:
    assert gat.get_env("GITHUB_ACTOR") == "test"
    assert gat.get_env("ANOTHER") == "another test"
