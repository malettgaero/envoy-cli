"""Tests for envoy.rotator."""
import pytest
from envoy.rotator import rotate_env, RotateResult


@pytest.fixture
def base_env():
    return {
        "DB_HOST": "localhost",
        "DB_PASS": "secret",
        "API_KEY": "abc123",
        "DEBUG": "true",
    }


def test_rotate_single_key(base_env):
    result = rotate_env(base_env, {"DB_PASS": "DATABASE_PASSWORD"})
    assert isinstance(result, RotateResult)
    assert "DATABASE_PASSWORD" in result.env
    assert result.env["DATABASE_PASSWORD"] == "secret"
    assert "DB_PASS" not in result.env


def test_rotate_removes_old_key_by_default(base_env):
    result = rotate_env(base_env, {"API_KEY": "SERVICE_API_KEY"})
    assert "API_KEY" not in result.env
    assert "SERVICE_API_KEY" in result.env


def test_rotate_keep_old_retains_source_key(base_env):
    result = rotate_env(base_env, {"DB_HOST": "DATABASE_HOST"}, keep_old=True)
    assert "DB_HOST" in result.env
    assert "DATABASE_HOST" in result.env
    assert result.env["DB_HOST"] == result.env["DATABASE_HOST"]


def test_rotate_missing_key_is_skipped(base_env):
    result = rotate_env(base_env, {"MISSING_KEY": "NEW_KEY"})
    assert result.skipped_count == 1
    assert result.rotated_count == 0
    entry = result.entries[0]
    assert entry.skipped
    assert "not found" in entry.skip_reason


def test_rotate_existing_new_key_skipped_without_overwrite(base_env):
    env = dict(base_env)
    env["DATABASE_HOST"] = "already_here"
    result = rotate_env(env, {"DB_HOST": "DATABASE_HOST"}, allow_overwrite=False)
    assert result.skipped_count == 1
    assert result.env["DATABASE_HOST"] == "already_here"


def test_rotate_existing_new_key_overwritten_with_flag(base_env):
    env = dict(base_env)
    env["DATABASE_HOST"] = "old_value"
    result = rotate_env(env, {"DB_HOST": "DATABASE_HOST"}, allow_overwrite=True)
    assert result.rotated_count == 1
    assert result.env["DATABASE_HOST"] == "localhost"


def test_rotate_multiple_keys(base_env):
    rotation_map = {"DB_HOST": "DATABASE_HOST", "DB_PASS": "DATABASE_PASSWORD"}
    result = rotate_env(base_env, rotation_map)
    assert result.rotated_count == 2
    assert result.skipped_count == 0
    assert "DATABASE_HOST" in result.env
    assert "DATABASE_PASSWORD" in result.env
    assert "DB_HOST" not in result.env
    assert "DB_PASS" not in result.env


def test_unrelated_keys_preserved(base_env):
    result = rotate_env(base_env, {"DB_HOST": "DATABASE_HOST"})
    assert result.env["API_KEY"] == "abc123"
    assert result.env["DEBUG"] == "true"


def test_summary_contains_rotated_and_skipped(base_env):
    result = rotate_env(base_env, {"DB_HOST": "DATABASE_HOST", "MISSING": "NEW"})
    summary = result.summary()
    assert "Rotated 1" in summary
    assert "skipped 1" in summary
    assert "OK" in summary
    assert "SKIP" in summary


def test_rotate_empty_env():
    result = rotate_env({}, {"FOO": "BAR"})
    assert result.rotated_count == 0
    assert result.skipped_count == 1
    assert result.env == {}


def test_entry_to_dict_skipped():
    result = rotate_env({}, {"OLD": "NEW"})
    d = result.entries[0].to_dict()
    assert d["skipped"] is True
    assert d["value"] is None
    assert d["skip_reason"] is not None
