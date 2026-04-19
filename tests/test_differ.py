"""Tests for envoy.differ."""
import pytest
from envoy.differ import diff_lines, DiffLine, DiffReport


A = """APP=hello
DEBUG=true
SECRET=abc
"""

B = """APP=hello
DEBUG=false
NEW_KEY=xyz
"""


def test_diff_lines_returns_report():
    report = diff_lines(A, B)
    assert isinstance(report, DiffReport)


def test_has_changes_when_different():
    report = diff_lines(A, B)
    assert report.has_changes


def test_no_changes_for_identical_text():
    report = diff_lines(A, A)
    assert not report.has_changes
    assert report.added == 0
    assert report.removed == 0


def test_added_count():
    report = diff_lines(A, B)
    assert report.added >= 1


def test_removed_count():
    report = diff_lines(A, B)
    assert report.removed >= 1


def test_equal_lines_present():
    report = diff_lines(A, B)
    equal_lines = [l for l in report.lines if l.tag == "equal"]
    assert any("APP=hello" in l.content for l in equal_lines)


def test_insert_lines_have_no_line_no_a():
    report = diff_lines(A, B)
    for line in report.lines:
        if line.tag == "insert":
            assert line.line_no_a is None
            assert line.line_no_b is not None


def test_delete_lines_have_no_line_no_b():
    report = diff_lines(A, B)
    for line in report.lines:
        if line.tag == "delete":
            assert line.line_no_b is None
            assert line.line_no_a is not None


def test_summary_format():
    report = diff_lines(A, B)
    s = report.summary()
    assert s.startswith("+")
    assert "-" in s


def test_to_dict_on_line():
    line = DiffLine("equal", 1, 1, "APP=hello")
    d = line.to_dict()
    assert d["tag"] == "equal"
    assert d["content"] == "APP=hello"


def test_empty_files_no_changes():
    report = diff_lines("", "")
    assert not report.has_changes


def test_added_from_empty():
    report = diff_lines("", "KEY=val\n")
    assert report.added == 1
    assert report.removed == 0
