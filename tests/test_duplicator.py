"""Tests for envoy.duplicator."""
import pytest
from envoy.duplicator import find_duplicates, DuplicateResult


def _lines(*text: str):
    """Helper – split a block of text into lines."""
    return list(text)


def test_no_duplicates_returns_empty_result():
    lines = _lines("FOO=bar", "BAZ=qux")
    result = find_duplicates(lines)
    assert not result.has_duplicates
    assert result.duplicates == []


def test_single_duplicate_detected():
    lines = _lines("FOO=first", "FOO=second")
    result = find_duplicates(lines)
    assert result.has_duplicates
    assert len(result.duplicates) == 1
    entry = result.duplicates[0]
    assert entry.key == "FOO"
    assert entry.occurrences == 2
    assert entry.lines == [1, 2]


def test_multiple_duplicates_detected():
    lines = _lines("A=1", "B=2", "A=3", "B=4", "C=5")
    result = find_duplicates(lines)
    assert result.has_duplicates
    keys = {e.key for e in result.duplicates}
    assert keys == {"A", "B"}


def test_comments_and_blanks_ignored():
    lines = _lines("# FOO=ignored", "", "FOO=real", "BAR=val")
    result = find_duplicates(lines)
    assert not result.has_duplicates


def test_triplicate_counted_correctly():
    lines = _lines("X=1", "X=2", "X=3")
    result = find_duplicates(lines)
    entry = result.duplicates[0]
    assert entry.occurrences == 3
    assert entry.lines == [1, 2, 3]


def test_summary_no_duplicates():
    result = find_duplicates(["A=1"])
    assert result.summary == "No duplicate keys found."


def test_summary_with_duplicates():
    lines = _lines("FOO=a", "FOO=b")
    result = find_duplicates(lines)
    assert "FOO" in result.summary
    assert "x2" in result.summary


def test_to_dict_structure():
    lines = _lines("KEY=v1", "KEY=v2")
    result = find_duplicates(lines)
    d = result.duplicates[0].to_dict()
    assert d["key"] == "KEY"
    assert d["occurrences"] == 2
    assert d["lines"] == [1, 2]


def test_line_numbers_are_correct_with_gaps():
    lines = _lines("A=1", "# comment", "", "A=2")
    result = find_duplicates(lines)
    assert result.has_duplicates
    assert result.duplicates[0].lines == [1, 4]


def test_empty_input_returns_no_duplicates():
    result = find_duplicates([])
    assert not result.has_duplicates
