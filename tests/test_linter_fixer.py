"""Tests for envoy.linter_fixer."""
import pytest
from envoy.linter_fixer import fix_env, FixResult


def _lines(*args):
    return list(args)


def test_fix_returns_fix_result():
    result = fix_env(_lines("KEY=value"))
    assert isinstance(result, FixResult)


def test_clean_file_no_changes():
    result = fix_env(_lines("KEY=value", "OTHER=123"))
    assert not result.changed
    assert result.changed_count == 0


def test_blank_lines_and_comments_preserved():
    lines = _lines("", "# comment", "KEY=val")
    result = fix_env(lines)
    assert result.lines[0] == ""
    assert result.lines[1] == "# comment"


def test_lowercase_key_uppercased():
    result = fix_env(_lines("mykey=hello"))
    assert result.changed
    assert result.lines[0] == "MYKEY=hello"


def test_value_whitespace_stripped():
    result = fix_env(_lines("KEY=  spaced  "))
    assert result.changed
    assert result.lines[0] == "KEY=spaced"


def test_key_and_value_both_fixed():
    result = fix_env(_lines("mykey=  value  "))
    assert result.changed
    assert result.lines[0] == "MYKEY=value"
    assert "key uppercased" in result.entries[0].reason
    assert "value whitespace stripped" in result.entries[0].reason


def test_entry_stores_original_and_fixed():
    result = fix_env(_lines("lower=val"))
    entry = result.entries[0]
    assert entry.original == "lower=val"
    assert entry.fixed == "LOWER=val"
    assert entry.line_number == 1


def test_multiple_fixes_counted():
    result = fix_env(_lines("a=1", "B=2", "c= 3 "))
    assert result.changed_count == 2


def test_summary_no_changes():
    result = fix_env(_lines("KEY=value"))
    assert result.summary() == "No fixes applied."


def test_summary_with_changes():
    result = fix_env(_lines("low=val"))
    assert "1 fix(es) applied" in result.summary()


def test_line_without_equals_skipped():
    result = fix_env(_lines("NOEQUALS"))
    assert not result.changed
    assert result.lines[0] == "NOEQUALS"


def test_to_dict_on_entry():
    result = fix_env(_lines("k= v "))
    d = result.entries[0].to_dict()
    assert "line_number" in d
    assert "original" in d
    assert "fixed" in d
    assert "reason" in d
