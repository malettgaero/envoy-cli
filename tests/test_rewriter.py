"""Tests for envoy.rewriter."""
import pytest
from envoy.rewriter import rewrite_env, RewriteResult, RewriteEntry


@pytest.fixture
def base_env():
    return {
        "DATABASE_URL": "postgres://localhost/mydb",
        "REDIS_URL": "redis://localhost:6379",
        "APP_NAME": "myapp",
        "DEBUG": "true",
    }


def test_rewrite_returns_rewrite_result(base_env):
    result = rewrite_env(base_env, "localhost", "prod-host")
    assert isinstance(result, RewriteResult)


def test_no_match_returns_unchanged(base_env):
    result = rewrite_env(base_env, "nonexistent", "replacement")
    assert not result.changed
    assert result.changed_count == 0
    assert result.env == base_env


def test_single_key_rewritten(base_env):
    result = rewrite_env(base_env, "localhost", "prod-host", keys=["DATABASE_URL"])
    assert result.changed
    assert result.env["DATABASE_URL"] == "postgres://prod-host/mydb"
    assert result.env["REDIS_URL"] == "redis://localhost:6379"  # untouched


def test_multiple_keys_rewritten(base_env):
    result = rewrite_env(base_env, "localhost", "prod-host")
    assert result.changed_count == 2
    assert result.env["DATABASE_URL"] == "postgres://prod-host/mydb"
    assert result.env["REDIS_URL"] == "redis://prod-host:6379"


def test_entry_fields_populated(base_env):
    result = rewrite_env(base_env, "localhost", "prod-host", keys=["DATABASE_URL"])
    entry = result.entries[0]
    assert isinstance(entry, RewriteEntry)
    assert entry.key == "DATABASE_URL"
    assert entry.original == "postgres://localhost/mydb"
    assert entry.rewritten == "postgres://prod-host/mydb"
    assert entry.pattern == "localhost"
    assert entry.replacement == "prod-host"


def test_to_dict_on_entry(base_env):
    result = rewrite_env(base_env, "localhost", "prod-host", keys=["DATABASE_URL"])
    d = result.entries[0].to_dict()
    assert set(d.keys()) == {"key", "original", "rewritten", "pattern", "replacement"}


def test_keys_filter_restricts_rewrites(base_env):
    result = rewrite_env(base_env, "localhost", "prod-host", keys=["REDIS_URL"])
    assert result.changed_count == 1
    assert result.env["REDIS_URL"] == "redis://prod-host:6379"
    assert result.env["DATABASE_URL"] == "postgres://localhost/mydb"


def test_missing_key_in_filter_is_skipped(base_env):
    result = rewrite_env(base_env, "localhost", "prod-host", keys=["MISSING_KEY"])
    assert not result.changed


def test_regex_mode_substitutes_pattern(base_env):
    result = rewrite_env(base_env, r":\d+", ":5432", keys=["REDIS_URL"], regex=True)
    assert result.env["REDIS_URL"] == "redis://localhost:5432"


def test_regex_mode_no_match_unchanged(base_env):
    result = rewrite_env(base_env, r"\d{5}", "00000", regex=True)
    assert not result.changed


def test_summary_no_changes(base_env):
    result = rewrite_env(base_env, "zzz", "yyy")
    assert result.summary() == "No values rewritten."


def test_summary_with_changes(base_env):
    result = rewrite_env(base_env, "localhost", "prod", keys=["DATABASE_URL"])
    summary = result.summary()
    assert "DATABASE_URL" in summary
    assert "->" in summary


def test_original_env_not_mutated(base_env):
    original_copy = dict(base_env)
    rewrite_env(base_env, "localhost", "prod-host")
    assert base_env == original_copy
