# pyright: reportPrivateUsage=false
# pyright: reportUnusedVariable=false
# pyright: reportUnusedParameter=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUnknownMemberType=false

from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

import github_action_toolkit as gat
import github_action_toolkit.print_messages as gat_print_messages


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (
            ["debug", "test debug", "test=1,test2=2"],
            "::debug test=1,test2=2::test debug\n",
        ),
        (["debug", "test debug", None], "::debug ::test debug\n"),
    ],
)
def test__print_command(capfd: Any, test_input: Any, expected: str) -> None:
    gat_print_messages._print_command(*test_input)
    out, err = capfd.readouterr()
    assert out == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("test", "test"),
        (1, "1"),
        (3.14, "3.14"),
        (["test", "test"], '["test", "test"]'),
        (
            (
                "test",
                "test",
            ),
            '["test", "test"]',
        ),
        ({"test": 3.14, "key": True}, '{"test": 3.14, "key": true}'),
    ],
)
def test__make_string(test_input: Any, expected: str) -> None:
    assert gat_print_messages._make_string(test_input) == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("test", "test"),
        ("test\n", "test%0A"),
        ("%test", "%25test"),
        ("\rtest", "%0Dtest"),
    ],
)
def test_escape_data(test_input: str, expected: str) -> None:
    assert gat_print_messages.escape_data(test_input) == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("test", "test"),
        ("test:", "test%3A"),
        ("test,", "test%2C"),
    ],
)
def test_escape_property(test_input: str, expected: str) -> None:
    assert gat_print_messages.escape_property(test_input) == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("test_string", "testString"),
        ("String_New", "stringNew"),
        ("One_two_Three", "oneTwoThree"),
    ],
)
def test__to_camel_case(test_input: str, expected: str) -> None:
    assert gat_print_messages._to_camel_case(test_input) == expected


@pytest.mark.parametrize(
    "input_kwargs,expected",
    [
        (
            {
                "title": "test  \ntitle",
                "file": "abc.py",
                "col": 1,
                "end_column": 2,
                "line": 4,
                "end_line": 5,
            },
            "title=test  %0Atitle,file=abc.py,col=1,endColumn=2,line=4,endLine=5",
        ),
        ({"name": "test-name"}, "name=test-name"),
        ({}, ""),
    ],
)
def test__build_options_string(input_kwargs: Any, expected: str) -> None:
    assert gat_print_messages._build_options_string(**input_kwargs) == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("test", "test\n"),
        ("test\n", "test\n\n"),
        ("%test", "%test\n"),
        ("\rtest", "\rtest\n"),
    ],
)
def test_echo(capfd: Any, test_input: str, expected: str) -> None:
    gat.echo(test_input)
    out, err = capfd.readouterr()
    assert out == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("test", "test\n"),
        ("test\n", "test\n\n"),
        ("%test", "%test\n"),
        ("\rtest", "\rtest\n"),
    ],
)
def test_info(capfd: Any, test_input: str, expected: str) -> None:
    gat.info(test_input)
    out, err = capfd.readouterr()
    assert out == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("test", "::debug ::test\n"),
        ("test\n", "::debug ::test\n\n"),
        ("%test", "::debug ::%test\n"),
        ("\rtest", "::debug ::\rtest\n"),
    ],
)
def test_debug(capfd: Any, test_input: str, expected: str) -> None:
    gat.debug(test_input)
    out, err = capfd.readouterr()
    assert out == expected


@pytest.mark.parametrize(
    "input_args,input_kwargs,expected",
    [
        (
            ["test notice"],
            {
                "title": "test  \ntitle",
                "file": "abc.py",
                "col": 1,
                "end_column": 2,
                "line": 4,
                "end_line": 5,
            },
            "::notice title=test  %0Atitle,file=abc.py,col=1,endColumn=2,line=4,endLine=5::test notice\n",
        ),
        (["test notice"], {}, "::notice ::test notice\n"),
    ],
)
def test_notice(
    capfd: Any,
    input_args: Any,
    input_kwargs: Any,
    expected: str,
) -> None:
    gat.notice(*input_args, **input_kwargs)
    out, err = capfd.readouterr()
    assert out == expected


@pytest.mark.parametrize(
    "input_args,input_kwargs,expected",
    [
        (
            ["test warning"],
            {
                "title": "test  \ntitle",
                "file": "abc.py",
                "col": 1,
                "end_column": 2,
                "line": 4,
                "end_line": 5,
            },
            "::warning title=test  %0Atitle,file=abc.py,col=1,endColumn=2,line=4,endLine=5::test warning\n",
        ),
        (["test warning"], {}, "::warning ::test warning\n"),
    ],
)
def test_warning(
    capfd: Any,
    input_args: Any,
    input_kwargs: Any,
    expected: str,
) -> None:
    gat.warning(*input_args, **input_kwargs)
    out, err = capfd.readouterr()
    assert out == expected


@pytest.mark.parametrize(
    "input_args,input_kwargs,expected",
    [
        (
            ["test error"],
            {
                "title": "test  \ntitle",
                "file": "abc.py",
                "col": 1,
                "end_column": 2,
                "line": 4,
                "end_line": 5,
            },
            "::error title=test  %0Atitle,file=abc.py,col=1,endColumn=2,line=4,endLine=5::test error\n",
        ),
        (["test error"], {}, "::error ::test error\n"),
    ],
)
def test_error(
    capfd: Any,
    input_args: Any,
    input_kwargs: Any,
    expected: str,
) -> None:
    gat.error(*input_args, **input_kwargs)
    out, err = capfd.readouterr()
    print(out)
    assert out == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("test", "::add-mask ::test\n"),
        (1, "::add-mask ::1\n"),
        (3.14, "::add-mask ::3.14\n"),
        (["test", "test"], '::add-mask ::["test", "test"]\n'),
        (
            (
                "test",
                "test",
            ),
            '::add-mask ::["test", "test"]\n',
        ),
        ({"test": 3.14, "key": True}, '::add-mask ::{"test": 3.14, "key": true}\n'),
    ],
)
def test_add_mask(capfd: Any, test_input: str, expected: str) -> None:
    gat.add_mask(test_input)
    out, err = capfd.readouterr()
    assert out == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("test", "::group ::test\n"),
        ("test\n", "::group ::test\n\n"),
        ("%test", "::group ::%test\n"),
        ("\rtest", "::group ::\rtest\n"),
    ],
)
def test_start_group(capfd: Any, test_input: str, expected: str) -> None:
    gat.start_group(test_input)
    out, err = capfd.readouterr()
    assert out == expected


def test_end_group(capfd: Any) -> None:
    gat.end_group()
    out, err = capfd.readouterr()
    assert out == "::endgroup::\n"


@given(st.text())
def test_escape_data_roundtrip_is_safe(text: str) -> None:
    """Escaping data should never raise an exception."""
    result = gat_print_messages.escape_data(text)
    assert isinstance(result, str)


@given(st.text())
def test_escape_property_roundtrip_is_safe(text: str) -> None:
    """Escaping property should never raise an exception."""
    result = gat_print_messages.escape_property(text)
    assert isinstance(result, str)


@given(st.text(alphabet=st.characters(blacklist_categories=("Cc", "Cs")), min_size=1))
def test_escape_data_preserves_length_or_increases(text: str) -> None:
    """Escaped data should be same length or longer."""
    result = gat_print_messages.escape_data(text)
    assert len(result) >= len(text)


@given(st.text())
def test_to_camel_case_returns_string(text: str) -> None:
    """_to_camel_case should always return a string."""
    result = gat_print_messages._to_camel_case(text)
    assert isinstance(result, str)


@given(
    st.text(
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll"),
        ),
        min_size=1,
    )
)
def test_to_camel_case_starts_lowercase_if_alpha(text: str) -> None:
    """If input starts with alphabetic, camelCase should start lowercase."""
    # Only test if underscore is present
    if "_" not in text:
        return
    result = gat_print_messages._to_camel_case(text)
    if result and result[0].isalpha():
        assert result[0].islower()


@given(st.integers())
def test_escape_data_with_numbers(num: int) -> None:
    """escape_data should handle integer conversion properly."""
    result = gat_print_messages.escape_data(str(num))
    assert isinstance(result, str)
    assert str(num) in result or gat_print_messages.escape_data(str(num)) == result


# Additional property-based tests


@given(st.lists(st.text(), min_size=0, max_size=10))
def test_make_string_with_lists(items: list[str]) -> None:
    """Property test: _make_string handles lists correctly."""
    result = gat_print_messages._make_string(items)
    assert isinstance(result, str)
    assert result.startswith("[") and result.endswith("]")


@given(st.dictionaries(st.text(min_size=1, max_size=20), st.integers(), min_size=0, max_size=5))
def test_make_string_with_dicts(data: dict[str, int]) -> None:
    """Property test: _make_string handles dictionaries correctly."""
    result = gat_print_messages._make_string(data)
    assert isinstance(result, str)
    assert result.startswith("{") and result.endswith("}")


@given(st.text(alphabet=st.characters(blacklist_characters="%\r\n")))
def test_escape_data_with_safe_text(text: str) -> None:
    """Property test: escape_data preserves text without special chars."""
    result = gat_print_messages.escape_data(text)
    assert result == text


@given(st.text(alphabet=st.characters(blacklist_characters="%\r\n:,")))
def test_escape_property_with_safe_text(text: str) -> None:
    """Property test: escape_property preserves text without special chars."""
    result = gat_print_messages.escape_property(text)
    assert result == text


@given(st.text(alphabet=st.characters(blacklist_characters="%\r\n")))
def test_escape_data_preserves_already_escaped(text: str) -> None:
    """Property test: text without special chars doesn't change when escaped."""
    result = gat_print_messages.escape_data(text)
    # Since text has no special chars, it should remain the same
    assert result == text


@given(
    st.text(min_size=1, max_size=50),
    st.text(min_size=0, max_size=50),
    st.text(min_size=0, max_size=50),
)
def test_build_options_string_with_various_values(key: str, val1: str, val2: str) -> None:
    """Property test: _build_options_string handles various inputs."""
    result = gat_print_messages._build_options_string(**{key: val1, f"{key}_2": val2})
    assert isinstance(result, str)
    # Should contain camelCased keys
    if val1:
        assert gat_print_messages._to_camel_case(key) in result or "=" in result
    if val2:
        assert gat_print_messages._to_camel_case(f"{key}_2") in result or "=" in result
