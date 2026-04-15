"""Tests for envoy.stripper."""
import pytest
from envoy.stripper import strip_env, StripResult


def _lines(*args: str):
    """Helper: turn bare strings into newline-terminated lines."""
    return [line + "\n" for line in args]


def test_clean_env_returns_unchanged():
    lines = _lines("KEY=value", "OTHER=123")
    result = strip_env(lines)
    assert not result.changed
    assert result.removed_count == 0
    assert result.cleaned_lines == lines


def test_blank_lines_removed():
    lines = _lines("KEY=value", "", "OTHER=123")
    result = strip_env(lines)
    assert result.changed
    assert result.removed_count == 1
    assert result.entries[0].reason == "blank"
    assert result.entries[0].line_number == 2
    assert len(result.cleaned_lines) == 2


def test_comment_lines_removed():
    lines = _lines("# This is a comment", "KEY=value")
    result = strip_env(lines)
    assert result.changed
    assert result.removed_count == 1
    assert result.entries[0].reason == "comment"
    assert result.entries[0].original == "# This is a comment"


def test_mixed_comments_and_blanks():
    lines = _lines("# header", "", "KEY=value", "", "# footer", "OTHER=abc")
    result = strip_env(lines)
    assert result.removed_count == 4
    comments = [e for e in result.entries if e.reason == "comment"]
    blanks = [e for e in result.entries if e.reason == "blank"]
    assert len(comments) == 2
    assert len(blanks) == 2
    assert len(result.cleaned_lines) == 2


def test_only_blank_lines_returns_empty_cleaned():
    lines = _lines("", "", "")
    result = strip_env(lines)
    assert result.changed
    assert result.cleaned_lines == []


def test_only_comments_returns_empty_cleaned():
    lines = _lines("# one", "# two")
    result = strip_env(lines)
    assert result.cleaned_lines == []
    assert result.removed_count == 2


def test_summary_no_changes():
    result = strip_env(_lines("KEY=val"))
    assert result.summary() == "No comments or blank lines found."


def test_summary_comments_only():
    result = strip_env(_lines("# comment", "KEY=val"))
    assert "1 comment(s)" in result.summary()


def test_summary_blanks_only():
    result = strip_env(_lines("", "KEY=val"))
    assert "1 blank line(s)" in result.summary()


def test_summary_both():
    result = strip_env(_lines("# c", "", "KEY=val"))
    summary = result.summary()
    assert "comment" in summary
    assert "blank" in summary


def test_to_dict_has_expected_keys():
    result = strip_env(_lines("# comment", "KEY=val"))
    d = result.entries[0].to_dict()
    assert set(d.keys()) == {"line_number", "original", "reason"}


def test_inline_comment_not_stripped():
    """Lines like KEY=value # note are key-value pairs, not comments."""
    lines = _lines("KEY=value # inline note")
    result = strip_env(lines)
    assert not result.changed
    assert len(result.cleaned_lines) == 1
