"""Tests for envoy.validator."""
import pytest

from envoy.validator import validate_env, ValidationResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _env(**kwargs: str):
    return dict(kwargs)


# ---------------------------------------------------------------------------
# Basic validation
# ---------------------------------------------------------------------------

def test_valid_env_passes():
    env = {"DATABASE_URL": "postgres://localhost/db", "SECRET_KEY": "abc123"}
    result = validate_env(env)
    assert result.is_valid
    assert result.summary() == "All checks passed."


def test_empty_value_flagged_by_default():
    env = {"API_KEY": "", "HOST": "localhost"}
    result = validate_env(env)
    assert not result.is_valid
    assert "API_KEY" in result.empty_keys


def test_empty_value_allowed_when_flag_set():
    env = {"API_KEY": ""}
    result = validate_env(env, allow_empty=True)
    assert result.is_valid


def test_invalid_key_name_flagged():
    env = {"valid_KEY": "x", "123BAD": "y", "GOOD_KEY": "z"}
    result = validate_env(env)
    # lowercase start and digit start are invalid
    assert "valid_KEY" in result.invalid_keys
    assert "123BAD" in result.invalid_keys
    assert "GOOD_KEY" not in result.invalid_keys


# ---------------------------------------------------------------------------
# Template-based validation
# ---------------------------------------------------------------------------

def test_missing_keys_detected():
    template = {"DB_URL": "", "SECRET": "", "PORT": ""}
    env = {"DB_URL": "postgres://localhost"}
    result = validate_env(env, template=template)
    assert "SECRET" in result.missing_keys
    assert "PORT" in result.missing_keys
    assert "DB_URL" not in result.missing_keys


def test_no_missing_keys_when_all_present():
    template = {"A": "", "B": ""}
    env = {"A": "1", "B": "2"}
    result = validate_env(env, template=template)
    assert result.missing_keys == []


def test_extra_keys_not_flagged_by_default():
    template = {"A": ""}
    env = {"A": "1", "EXTRA": "2"}
    result = validate_env(env, template=template)
    assert result.extra_keys == []


def test_extra_keys_flagged_in_strict_mode():
    template = {"A": ""}
    env = {"A": "1", "EXTRA": "2"}
    result = validate_env(env, template=template, strict=True)
    assert "EXTRA" in result.extra_keys


# ---------------------------------------------------------------------------
# Summary output
# ---------------------------------------------------------------------------

def test_summary_lists_all_issues():
    template = {"REQUIRED": ""}
    env = {"EMPTY_VAL": "", "bad_key": "x"}
    result = validate_env(env, template=template)
    summary = result.summary()
    assert "Missing keys" in summary
    assert "REQUIRED" in summary
    assert "Empty values" in summary
    assert "EMPTY_VAL" in summary
    assert "Invalid key names" in summary
    assert "bad_key" in summary
