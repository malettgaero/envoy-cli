"""Tests for envoy.linter."""
import pytest
from envoy.linter import lint_env, LintIssue, LintResult


def _lines(*raw: str):
    """Helper: turn positional strings into a list of lines."""
    return list(raw)


# ---------------------------------------------------------------------------
# Passing cases
# ---------------------------------------------------------------------------

def test_clean_file_passes():
    result = lint_env(_lines("APP_NAME=myapp\n", "DEBUG=false\n"))
    assert result.passed
    assert result.summary() == "No lint issues found."


def test_blank_lines_and_comments_ignored():
    result = lint_env(_lines("", "# comment\n", "PORT=8080\n"))
    assert result.passed


def test_double_quoted_value_passes():
    result = lint_env(_lines('SECRET="abc123"\n'))
    assert result.passed


# ---------------------------------------------------------------------------
# W001 — uppercase key
# ---------------------------------------------------------------------------

def test_lowercase_key_flagged():
    result = lint_env(_lines("app_name=myapp\n"))
    assert not result.passed
    codes = [i.code for i in result.issues]
    assert "W001" in codes


def test_mixed_case_key_flagged():
    result = lint_env(_lines("AppName=myapp\n"))
    codes = [i.code for i in result.issues]
    assert "W001" in codes


# ---------------------------------------------------------------------------
# W002 — whitespace around '='
# ---------------------------------------------------------------------------

def test_space_before_equals_flagged():
    result = lint_env(_lines("APP_NAME =myapp\n"))
    codes = [i.code for i in result.issues]
    assert "W002" in codes


def test_space_after_equals_flagged():
    result = lint_env(_lines("APP_NAME= myapp\n"))
    codes = [i.code for i in result.issues]
    assert "W002" in codes


# ---------------------------------------------------------------------------
# W003 — single quotes
# ---------------------------------------------------------------------------

def test_single_quoted_value_flagged():
    result = lint_env(_lines("SECRET='abc123'\n"))
    codes = [i.code for i in result.issues]
    assert "W003" in codes


# ---------------------------------------------------------------------------
# W004 — trailing whitespace
# ---------------------------------------------------------------------------

def test_trailing_whitespace_in_value_flagged():
    result = lint_env(_lines("APP_NAME=myapp   \n"))
    codes = [i.code for i in result.issues]
    assert "W004" in codes


def test_trailing_whitespace_inside_quotes_not_flagged():
    # Quoted values with trailing spaces are intentional
    result = lint_env(_lines('APP_NAME="myapp   "\n'))
    assert result.passed


# ---------------------------------------------------------------------------
# LintResult helpers
# ---------------------------------------------------------------------------

def test_summary_lists_all_issues():
    result = lint_env(_lines("bad_key= value   \n"))
    summary = result.summary()
    assert "lint issue" in summary
    assert "W001" in summary
