"""Tests for envoy.pruner."""
import pytest
from envoy.pruner import prune_env, PruneResult


@pytest.fixture
def base_env():
    return {
        "APP_NAME": "myapp",
        "APP_SECRET": "s3cr3t",
        "DB_HOST": "localhost",
        "DB_PASSWORD": "pass123",
        "DEBUG": "true",
        "LOG_LEVEL": "info",
    }


def test_prune_returns_prune_result(base_env):
    result = prune_env(base_env)
    assert isinstance(result, PruneResult)


def test_no_keys_no_patterns_keeps_all(base_env):
    result = prune_env(base_env)
    assert result.kept == base_env
    assert result.pruned_count == 0
    assert not result.changed


def test_exact_key_removed(base_env):
    result = prune_env(base_env, keys=["DEBUG"])
    assert "DEBUG" not in result.kept
    assert result.pruned_count == 1
    assert result.pruned[0].key == "DEBUG"
    assert result.pruned[0].reason == "exact"


def test_multiple_exact_keys_removed(base_env):
    result = prune_env(base_env, keys=["DEBUG", "LOG_LEVEL"])
    assert "DEBUG" not in result.kept
    assert "LOG_LEVEL" not in result.kept
    assert result.pruned_count == 2


def test_pattern_removes_matching_keys(base_env):
    result = prune_env(base_env, patterns=["DB_*"])
    assert "DB_HOST" not in result.kept
    assert "DB_PASSWORD" not in result.kept
    assert result.pruned_count == 2


def test_pattern_reason_includes_pattern_name(base_env):
    result = prune_env(base_env, patterns=["APP_*"])
    for entry in result.pruned:
        assert entry.reason == "pattern:APP_*"


def test_exact_and_pattern_combined(base_env):
    result = prune_env(base_env, keys=["DEBUG"], patterns=["DB_*"])
    assert result.pruned_count == 3
    assert "APP_NAME" in result.kept


def test_nonexistent_key_ignored(base_env):
    result = prune_env(base_env, keys=["NONEXISTENT"])
    assert result.pruned_count == 0
    assert result.kept == base_env


def test_original_env_unchanged(base_env):
    original_copy = dict(base_env)
    prune_env(base_env, keys=["DEBUG"], patterns=["DB_*"])
    assert base_env == original_copy


def test_changed_flag_true_when_pruned(base_env):
    result = prune_env(base_env, keys=["DEBUG"])
    assert result.changed is True


def test_summary_no_changes():
    result = prune_env({"A": "1"})
    assert result.summary() == "No keys pruned."


def test_summary_lists_pruned_keys(base_env):
    result = prune_env(base_env, keys=["DEBUG", "LOG_LEVEL"])
    summary = result.summary()
    assert "DEBUG" in summary
    assert "LOG_LEVEL" in summary
    assert "2 key(s)" in summary


def test_wildcard_star_matches_all(base_env):
    result = prune_env(base_env, patterns=["*"])
    assert result.kept == {}
    assert result.pruned_count == len(base_env)
