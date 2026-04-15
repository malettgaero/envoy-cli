"""Tests for envoy.sanitizer."""
import pytest
from envoy.sanitizer import sanitize_env, SanitizeResult


def _env(**kwargs: str) -> dict:
    return dict(kwargs)


def test_clean_env_returns_unchanged():
    env = _env(HOST="localhost", PORT="5432")
    result = sanitize_env(env)
    assert result.env == env
    assert not result.changed
    assert result.changed_count == 0


def test_leading_whitespace_stripped():
    env = _env(KEY="  value")
    result = sanitize_env(env)
    assert result.env["KEY"] == "value"
    assert result.changed


def test_trailing_whitespace_stripped():
    env = _env(KEY="value   ")
    result = sanitize_env(env)
    assert result.env["KEY"] == "value"


def test_both_sides_stripped():
    env = _env(KEY="  hello world  ")
    result = sanitize_env(env)
    assert result.env["KEY"] == "hello world"


def test_embedded_newline_removed():
    env = _env(MSG="line1\nline2")
    result = sanitize_env(env)
    assert "\n" not in result.env["MSG"]
    assert result.changed


def test_carriage_return_removed():
    env = _env(MSG="value\r")
    result = sanitize_env(env)
    assert "\r" not in result.env["MSG"]


def test_control_char_removed():
    env = _env(KEY="val\x01ue")
    result = sanitize_env(env)
    assert "\x01" not in result.env["KEY"]
    assert result.changed


def test_strip_newlines_disabled():
    env = _env(MSG="line1\nline2")
    result = sanitize_env(env, strip_newlines=False)
    assert "\n" in result.env["MSG"]


def test_strip_control_chars_disabled():
    env = _env(KEY="val\x01ue")
    result = sanitize_env(env, strip_control_chars=False)
    assert "\x01" in result.env["KEY"]


def test_strip_whitespace_disabled():
    env = _env(KEY="  value  ")
    result = sanitize_env(env, strip_leading_trailing_whitespace=False)
    assert result.env["KEY"] == "  value  "


def test_replacement_char_used():
    env = _env(KEY="val\nue")
    result = sanitize_env(env, replacement="_")
    assert result.env["KEY"] == "val_ue"


def test_issues_recorded_on_entry():
    env = _env(KEY="  val\nue  ")
    result = sanitize_env(env)
    entry = next(e for e in result.entries if e.key == "KEY")
    assert any("whitespace" in i for i in entry.issues)
    assert any("newline" in i for i in entry.issues)


def test_summary_no_changes():
    result = sanitize_env(_env(A="ok"))
    assert "No sanitization" in result.summary()


def test_summary_with_changes():
    result = sanitize_env(_env(A="  bad\x01val  "))
    assert "sanitized" in result.summary()
    assert "A" in result.summary()


def test_changed_count_multiple_keys():
    env = _env(A="  bad", B="good", C="also\nbad")
    result = sanitize_env(env)
    assert result.changed_count == 2


def test_to_dict_shape():
    env = _env(KEY="  val  ")
    result = sanitize_env(env)
    d = result.entries[0].to_dict()
    assert set(d.keys()) == {"key", "original", "sanitized", "issues"}
