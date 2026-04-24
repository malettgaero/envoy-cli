"""Tests for envoy/formatter.py."""
import pytest
from envoy.formatter import format_env, FormatResult, FormatEntry


def _lines(*pairs: str) -> list[str]:
    """Build a list of raw lines from 'KEY=VALUE' strings."""
    return [p + "\n" for p in pairs]


def test_format_returns_format_result():
    result = format_env(_lines("FOO=bar"))
    assert isinstance(result, FormatResult)


def test_no_changes_when_already_canonical():
    result = format_env(_lines("FOO=bar", "BAZ=qux"))
    assert not result.changed
    assert result.changed_count == 0


def test_space_around_equals_applied():
    result = format_env(_lines("FOO=bar"), space_around_equals=True)
    assert result.changed
    assert result.entries[0].formatted_line == "FOO = bar"


def test_no_space_around_equals_default():
    result = format_env(_lines("FOO=bar"))
    assert result.entries[0].formatted_line == "FOO=bar"


def test_uppercase_keys_applied():
    result = format_env(_lines("foo=bar"), uppercase_keys=True)
    assert result.entries[0].key == "FOO"
    assert result.entries[0].formatted_line == "FOO=bar"


def test_uppercase_keys_marks_changed():
    result = format_env(_lines("foo=bar"), uppercase_keys=True)
    assert result.entries[0].changed


def test_quote_values_with_space():
    result = format_env(_lines("MSG=hello world"), quote_values=True)
    assert result.entries[0].formatted_line == 'MSG="hello world"'


def test_quote_values_no_space_unchanged():
    result = format_env(_lines("FOO=bar"), quote_values=True)
    # No space in value — should not add quotes
    assert result.entries[0].formatted_line == "FOO=bar"


def test_already_quoted_value_not_double_quoted():
    result = format_env(_lines('FOO="hello world"'), quote_values=True)
    assert result.entries[0].formatted_line == 'FOO="hello world"'


def test_comments_preserved():
    lines = ["# this is a comment\n", "FOO=bar\n"]
    result = format_env(lines)
    assert "# this is a comment" in result.preserved_lines
    assert len(result.entries) == 1


def test_blank_lines_preserved():
    lines = ["\n", "FOO=bar\n", "\n"]
    result = format_env(lines)
    assert result.preserved_lines.count("") == 2


def test_line_without_equals_preserved():
    lines = ["NOTAKEY\n", "FOO=bar\n"]
    result = format_env(lines)
    assert "NOTAKEY" in result.preserved_lines
    assert len(result.entries) == 1


def test_changed_count_correct():
    result = format_env(_lines("foo=bar", "BAZ=qux"), uppercase_keys=True)
    # 'foo' -> 'FOO' changes; 'BAZ' is already uppercase
    assert result.changed_count == 1


def test_env_property_returns_dict():
    result = format_env(_lines("FOO=bar", "BAZ=qux"))
    assert result.env == {"FOO": "bar", "BAZ": "qux"}


def test_summary_no_changes():
    result = format_env(_lines("FOO=bar"))
    assert "No formatting" in result.summary()


def test_summary_with_changes():
    result = format_env(_lines("foo=bar"), uppercase_keys=True)
    assert "reformatted" in result.summary()


def test_to_dict_on_entry():
    result = format_env(_lines("FOO=bar"))
    d = result.entries[0].to_dict()
    assert set(d.keys()) == {"key", "original_line", "formatted_line", "changed"}


def test_multiple_options_combined():
    result = format_env(_lines("foo=hello world"), uppercase_keys=True, quote_values=True)
    entry = result.entries[0]
    assert entry.key == "FOO"
    assert entry.formatted_line == 'FOO="hello world"'
    assert entry.changed
