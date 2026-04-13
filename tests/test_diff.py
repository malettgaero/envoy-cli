"""Tests for envoy.diff module."""

import pytest

from envoy.diff import diff_envs, DiffResult, _mask


BASE = {
    "APP_NAME": "myapp",
    "DEBUG": "true",
    "SECRET_KEY": "base-secret",
    "REMOVED_KEY": "old-value",
}

TARGET = {
    "APP_NAME": "myapp",
    "DEBUG": "false",
    "SECRET_KEY": "new-secret",
    "ADDED_KEY": "brand-new",
}


def test_diff_detects_added_keys():
    result = diff_envs(BASE, TARGET)
    assert "ADDED_KEY" in result.added


def test_diff_detects_removed_keys():
    result = diff_envs(BASE, TARGET)
    assert "REMOVED_KEY" in result.removed


def test_diff_detects_changed_keys():
    result = diff_envs(BASE, TARGET)
    assert "DEBUG" in result.changed
    assert "SECRET_KEY" in result.changed
    assert result.changed["DEBUG"] == ("true", "false")


def test_diff_unchanged_keys():
    result = diff_envs(BASE, TARGET)
    assert "APP_NAME" in result.unchanged


def test_diff_has_changes_flag():
    result = diff_envs(BASE, TARGET)
    assert result.has_changes is True


def test_diff_no_changes():
    result = diff_envs(BASE, BASE)
    assert result.has_changes is False
    assert "(no changes)" in result.summary()


def test_diff_summary_contains_symbols():
    result = diff_envs(BASE, TARGET)
    summary = result.summary()
    assert "+" in summary  # added
    assert "-" in summary  # removed
    assert "~" in summary  # changed


def test_mask_short_value():
    assert _mask("abc") == "***"


def test_mask_long_value():
    masked = _mask("supersecret", visible=4)
    assert masked.startswith("supe")
    assert "*" in masked
    assert "supersecret" not in masked
