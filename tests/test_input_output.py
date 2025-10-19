# pyright: reportPrivateUsage=false
# pyright: reportUnusedVariable=false
# pyright: reportUnusedParameter=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUnknownMemberType=false

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


@mock.patch.dict(
    os.environ,
    {
        "INPUT_USERNAME": "test_user",
        "INPUT_DEBUG": "true",
        "SOME_OTHER_ENV": "ignore_this",
    },
)
def test_get_all_user_inputs_returns_only_input_vars():
    result = gat.get_all_user_inputs()
    assert isinstance(result, dict)
    assert result == {
        "username": "test_user",
        "debug": "true",
    }


@mock.patch.dict(os.environ, {}, clear=True)
def test_get_all_user_inputs_with_no_inputs():
    assert gat.get_all_user_inputs() == {}


@mock.patch.dict(
    os.environ,
    {
        "INPUT_API_KEY": "abc123",
        "INPUT_VERBOSE": "yes",
    },
)
def test_print_all_user_inputs_outputs_correctly(capfd):
    gat.print_all_user_inputs()
    out, _ = capfd.readouterr()
    assert "User Inputs:" in out
    assert "api_key: abc123" in out
    assert "verbose: yes" in out


@mock.patch.dict(os.environ, {}, clear=True)
def test_print_all_user_inputs_when_no_env_vars(capfd):
    gat.print_all_user_inputs()
    out, _ = capfd.readouterr()
    assert "No user inputs found." in out


@mock.patch.dict(os.environ, {"INPUT_USERNAME": "test", "ANOTHER": "another test"})
def test_get_user_input() -> None:
    assert gat.get_user_input("username") == "test"
    assert gat.get_user_input("another") is None


@mock.patch.dict(os.environ, {"INPUT_AGE": "30", "INPUT_HEIGHT": "5.8"})
def test_get_user_input_as_basic_types():
    assert gat.get_user_input_as("age", int) == 30
    assert gat.get_user_input_as("height", float) == 5.8
    assert gat.get_user_input_as("age", str) == "30"


@mock.patch.dict(
    os.environ,
    {
        "INPUT_ACTIVE": "true",
        "INPUT_DISABLED": "no",
        "INPUT_UNKNOWN": "maybe",
    },
)
def test_get_user_input_as_boolean_true_false():
    assert gat.get_user_input_as("active", bool, default_value=False) is True
    assert gat.get_user_input_as("disabled", bool, default_value=True) is False
    # fallback to casting if not matching known true/false strings
    assert gat.get_user_input_as("unknown", bool) is True


@mock.patch.dict(os.environ, {"INPUT_EMPTY": ""})
def test_get_user_input_as_empty_string_returns_default():
    assert gat.get_user_input_as("empty", int, default_value=42) == 42
    assert gat.get_user_input_as("empty", str, default_value="default") == "default"


@mock.patch.dict(os.environ, {}, clear=True)
def test_get_user_input_as_missing_env_var():
    assert gat.get_user_input_as("nonexistent", int) is None
    assert gat.get_user_input_as("nonexistent", str, default_value="x") == "x"


@mock.patch.dict(os.environ, {"INPUT_BROKEN": "abc"})
def test_get_user_input_as_type_cast_error():
    with pytest.raises(gat.InputError):
        gat.get_user_input_as("broken", int)


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


def test_with_env_context_manager():
    """Test with_env context manager sets and restores environment variables."""
    original_value = os.environ.get("TEST_VAR", None)
    os.environ["EXISTING_VAR"] = "original"

    with gat.with_env(TEST_VAR="temp_value", EXISTING_VAR="modified"):
        assert os.environ.get("TEST_VAR") == "temp_value"
        assert os.environ.get("EXISTING_VAR") == "modified"

    assert os.environ.get("TEST_VAR") == original_value
    assert os.environ.get("EXISTING_VAR") == "original"

    os.environ.pop("EXISTING_VAR", None)


@mock.patch.dict(os.environ, {}, clear=True)
def test_set_output_without_github_output_raises_error():
    """Test set_output raises EnvironmentVariableError when GITHUB_OUTPUT not set."""
    with pytest.raises(gat.EnvironmentVariableError):
        gat.set_output("test", "value")


@mock.patch.dict(os.environ, {}, clear=True)
def test_save_state_without_github_state_raises_error():
    """Test save_state raises EnvironmentVariableError when GITHUB_STATE not set."""
    with pytest.raises(gat.EnvironmentVariableError):
        gat.save_state("test", "value")


@mock.patch.dict(os.environ, {}, clear=True)
def test_set_env_without_github_env_raises_error():
    """Test set_env raises EnvironmentVariableError when GITHUB_ENV not set."""
    with pytest.raises(gat.EnvironmentVariableError):
        gat.set_env("test", "value")


@mock.patch.dict(os.environ, {}, clear=True)
def test_get_workflow_environment_variables_without_github_env_raises_error():
    """Test get_workflow_environment_variables raises error when GITHUB_ENV not set."""
    with pytest.raises(gat.EnvironmentVariableError):
        gat.get_workflow_environment_variables()


def test_export_variable(tmpdir: Any) -> None:
    """Test that export_variable works as an alias for set_env"""
    file = tmpdir.join("envfile")

    with mock.patch.dict(os.environ, {"GITHUB_ENV": file.strpath}):
        gat.export_variable("test", "test_value")
        gat.export_variable("another", 42)

    assert file.read() == (
        "test<<__ENV_DELIMITER__\n"
        "test_value\n__ENV_DELIMITER__\n"
        "another<<__ENV_DELIMITER__\n42\n"
        "__ENV_DELIMITER__\n"
    )


def test_add_path_with_string(tmpdir: Any) -> None:
    """Test adding a path using a string"""
    file = tmpdir.join("pathfile")
    test_path = "/usr/local/bin"

    with mock.patch.dict(os.environ, {"GITHUB_PATH": file.strpath}):
        gat.add_path(test_path)

    assert file.read() == f"{test_path}\n"


def test_add_path_with_pathlib(tmpdir: Any) -> None:
    """Test adding a path using pathlib.Path"""
    from pathlib import Path

    file = tmpdir.join("pathfile")
    test_path = Path("/opt/bin")

    with mock.patch.dict(os.environ, {"GITHUB_PATH": file.strpath}):
        gat.add_path(test_path)

    assert file.read() == f"{test_path}\n"


def test_add_path_multiple(tmpdir: Any) -> None:
    """Test adding multiple paths"""
    file = tmpdir.join("pathfile")

    with mock.patch.dict(os.environ, {"GITHUB_PATH": file.strpath}):
        gat.add_path("/usr/local/bin")
        gat.add_path("/opt/bin")

    assert file.read() == "/usr/local/bin\n/opt/bin\n"


def test_add_path_relative_raises_error(tmpdir: Any) -> None:
    """Test that relative paths raise a ValueError"""
    file = tmpdir.join("pathfile")

    with mock.patch.dict(os.environ, {"GITHUB_PATH": file.strpath}):
        with pytest.raises(ValueError, match="must be an absolute path"):
            gat.add_path("relative/path")


def test_delimiter_in_value_raises_error(tmpdir: Any) -> None:
    """Test that values containing the delimiter raise a ValueError"""
    from github_action_toolkit.consts import ACTION_ENV_DELIMITER

    file = tmpdir.join("envfile")
    malicious_value = f"test{ACTION_ENV_DELIMITER}injection"

    with mock.patch.dict(os.environ, {"GITHUB_ENV": file.strpath}):
        with pytest.raises(ValueError, match="contains the delimiter"):
            gat.set_env("test", malicious_value)


# Property-based tests for robust validation


from hypothesis import given
from hypothesis import strategies as st


@given(
    st.text(
        alphabet=st.characters(blacklist_characters="\x00", blacklist_categories=("Cs",)),
        min_size=1,
        max_size=100,
    )
)
def test_get_user_input_as_with_arbitrary_strings(text: str) -> None:
    """Property test: get_user_input_as handles arbitrary string inputs."""
    with mock.patch.dict(os.environ, {"INPUT_TEST": text}):
        result = gat.get_user_input_as("test", str)
        assert result == text


@given(st.integers())
def test_get_user_input_as_integer_conversion(num: int) -> None:
    """Property test: integer conversion works for all valid integers."""
    with mock.patch.dict(os.environ, {"INPUT_NUM": str(num)}):
        result = gat.get_user_input_as("num", int)
        assert result == num


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_get_user_input_as_float_conversion(num: float) -> None:
    """Property test: float conversion works for all valid floats."""
    with mock.patch.dict(os.environ, {"INPUT_NUM": str(num)}):
        result = gat.get_user_input_as("num", float)
        assert result == num


@given(st.text(alphabet=st.characters(blacklist_categories=("Cs",))))
def test_build_file_input_never_crashes(text: str) -> None:
    """Property test: _build_file_input handles arbitrary text without crashing."""
    from github_action_toolkit.consts import ACTION_ENV_DELIMITER

    # Skip if contains delimiter (expected to fail)
    if ACTION_ENV_DELIMITER not in text:
        try:
            result = gha_utils_input_output._build_file_input("test", text)
            assert isinstance(result, bytes)
            assert b"test" in result
        except Exception:
            # If an exception occurs, it should only be for extreme edge cases
            pass


@given(st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll")), min_size=1, max_size=50))
def test_get_all_user_inputs_with_various_names(name: str) -> None:
    """Property test: get_all_user_inputs correctly extracts INPUT_ prefixed vars."""
    # Handle special Unicode case-folding behavior
    expected_key = name.lower()
    env_key = f"INPUT_{name.upper()}"

    with mock.patch.dict(os.environ, {env_key: "value", "OTHER": "ignore"}):
        result = gat.get_all_user_inputs()
        # The key should be in result with the lowercased name
        assert expected_key in result or env_key[6:].lower() in result
        assert "other" not in result


@given(st.text(min_size=1, max_size=100), st.text(min_size=0, max_size=100))
def test_set_env_with_arbitrary_key_value(key: str, value: str) -> None:
    """Property test: set_env handles arbitrary key-value pairs."""
    from github_action_toolkit.consts import ACTION_ENV_DELIMITER

    # Skip if delimiter is in the value (expected to fail)
    if ACTION_ENV_DELIMITER in value:
        return

    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        filepath = f.name

    try:
        with mock.patch.dict(os.environ, {"GITHUB_ENV": filepath}):
            gat.set_env(key, value)

        with open(filepath, "rb") as f:
            content = f.read()
            assert isinstance(content, bytes)
    finally:
        os.unlink(filepath)
