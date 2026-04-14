"""Tests for envoy.trimmer."""
import pytest
from envoy.trimmer import trim_env, TrimEntry, TrimResult


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _env(**kwargs: str):
    return dict(kwargs)


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_clean_env_returns_unchanged():
    env = _env(HOST="localhost", PORT="5432")
    result = trim_env(env)
    assert result.env == env
    assert not result.changed
    assert result.changed_count == 0


def test_trailing_space_detected():
    env = _env(HOST="localhost   ")
    result = trim_env(env)
    assert result.changed
    assert result.env["HOST"] == "localhost"
    assert len(result.entries) == 1
    assert result.entries[0].key == "HOST"
    assert result.entries[0].original == "localhost   "
    assert result.entries[0].trimmed == "localhost"


def test_leading_space_detected():
    env = _env(KEY="  value")
    result = trim_env(env)
    assert result.env["KEY"] == "value"
    assert result.changed_count == 1


def test_both_sides_trimmed():
    env = _env(SECRET="  abc  ")
    result = trim_env(env)
    assert result.env["SECRET"] == "abc"


def test_multiple_keys_partially_dirty():
    env = _env(A="clean", B=" dirty ", C="also clean", D="\ttab\t")
    result = trim_env(env)
    assert result.changed_count == 2
    dirty_keys = {e.key for e in result.entries}
    assert dirty_keys == {"B", "D"}
    assert result.env["A"] == "clean"
    assert result.env["B"] == "dirty"
    assert result.env["D"] == "tab"


def test_empty_value_stays_empty():
    env = _env(EMPTY="")
    result = trim_env(env)
    assert result.env["EMPTY"] == ""
    assert not result.changed


def test_whitespace_only_value_becomes_empty():
    env = _env(BLANK="   ")
    result = trim_env(env)
    assert result.env["BLANK"] == ""
    assert result.changed


def test_summary_no_changes():
    result = trim_env(_env(X="ok"))
    assert "No trailing" in result.summary()


def test_summary_with_changes():
    result = trim_env(_env(X="value "))
    summary = result.summary()
    assert "1 key(s) trimmed" in summary
    assert "X" in summary


def test_to_dict_contains_expected_keys():
    entry = TrimEntry(key="FOO", original="bar ", trimmed="bar")
    d = entry.to_dict()
    assert d["key"] == "FOO"
    assert "original" in d
    assert "trimmed" in d


def test_original_env_not_mutated():
    env = _env(K="value  ")
    original_copy = dict(env)
    trim_env(env)
    assert env == original_copy
