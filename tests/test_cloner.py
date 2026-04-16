"""Tests for envoy.cloner."""
import pytest
from envoy.cloner import clone_env


@pytest.fixture
def base_env():
    return {"DB_HOST": "localhost", "DB_PORT": "5432", "APP_DEBUG": "true"}


def test_clone_single_key(base_env):
    result = clone_env(base_env, {"DB_HOST": "DATABASE_HOST"})
    assert result.env["DATABASE_HOST"] == "localhost"
    assert result.env["DB_HOST"] == "localhost"  # original kept
    assert result.cloned_count == 1


def test_clone_preserves_other_keys(base_env):
    result = clone_env(base_env, {"DB_HOST": "DATABASE_HOST"})
    assert "DB_PORT" in result.env
    assert "APP_DEBUG" in result.env


def test_clone_multiple_keys(base_env):
    result = clone_env(base_env, {"DB_HOST": "HOST_COPY", "DB_PORT": "PORT_COPY"})
    assert result.cloned_count == 2
    assert result.env["HOST_COPY"] == "localhost"
    assert result.env["PORT_COPY"] == "5432"


def test_move_removes_source(base_env):
    result = clone_env(base_env, {"DB_HOST": "DATABASE_HOST"}, move=True)
    assert "DB_HOST" not in result.env
    assert result.env["DATABASE_HOST"] == "localhost"
    assert result.entries[0].removed_source is True


def test_missing_source_key_skipped(base_env):
    result = clone_env(base_env, {"MISSING_KEY": "NEW_KEY"})
    assert result.cloned_count == 0
    assert result.skipped_count == 1
    assert "MISSING_KEY" in result.skipped
    assert "NEW_KEY" not in result.env


def test_no_overwrite_skips_existing_target(base_env):
    env = {**base_env, "DATABASE_HOST": "existing"}
    result = clone_env(env, {"DB_HOST": "DATABASE_HOST"}, overwrite=False)
    assert result.env["DATABASE_HOST"] == "existing"
    assert result.skipped_count == 1


def test_overwrite_replaces_existing_target(base_env):
    env = {**base_env, "DATABASE_HOST": "old"}
    result = clone_env(env, {"DB_HOST": "DATABASE_HOST"}, overwrite=True)
    assert result.env["DATABASE_HOST"] == "localhost"
    assert result.cloned_count == 1


def test_summary_no_skipped(base_env):
    result = clone_env(base_env, {"DB_HOST": "DATABASE_HOST"})
    assert "1 key(s) cloned" in result.summary()
    assert "skipped" not in result.summary()


def test_summary_with_skipped(base_env):
    result = clone_env(base_env, {"MISSING": "X"})
    assert "skipped" in result.summary()


def test_entry_to_dict(base_env):
    result = clone_env(base_env, {"DB_HOST": "DATABASE_HOST"})
    d = result.entries[0].to_dict()
    assert d["source_key"] == "DB_HOST"
    assert d["target_key"] == "DATABASE_HOST"
    assert d["value"] == "localhost"
    assert d["removed_source"] is False


def test_empty_mapping_returns_unchanged(base_env):
    result = clone_env(base_env, {})
    assert result.env == base_env
    assert result.cloned_count == 0
