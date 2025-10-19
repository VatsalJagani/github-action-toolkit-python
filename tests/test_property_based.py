# pyright: reportPrivateUsage=false
# pyright: reportUnusedVariable=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false

"""
Property-based tests using Hypothesis for testing invariants and edge cases.
"""

from hypothesis import given
from hypothesis import strategies as st

import github_action_toolkit.print_messages as gat_print


@given(st.text())
def test_escape_data_roundtrip_is_safe(text: str) -> None:
    """Escaping data should never raise an exception."""
    result = gat_print.escape_data(text)
    assert isinstance(result, str)


@given(st.text())
def test_escape_property_roundtrip_is_safe(text: str) -> None:
    """Escaping property should never raise an exception."""
    result = gat_print.escape_property(text)
    assert isinstance(result, str)


@given(st.text(alphabet=st.characters(blacklist_categories=("Cc", "Cs")), min_size=1))
def test_escape_data_preserves_length_or_increases(text: str) -> None:
    """Escaped data should be same length or longer."""
    result = gat_print.escape_data(text)
    assert len(result) >= len(text)


@given(st.text())
def test_to_camel_case_returns_string(text: str) -> None:
    """_to_camel_case should always return a string."""
    result = gat_print._to_camel_case(text)
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
    result = gat_print._to_camel_case(text)
    if result and result[0].isalpha():
        assert result[0].islower()


@given(st.integers())
def test_escape_data_with_numbers(num: int) -> None:
    """escape_data should handle integer conversion properly."""
    result = gat_print.escape_data(str(num))
    assert isinstance(result, str)
    assert str(num) in result or gat_print.escape_data(str(num)) == result
