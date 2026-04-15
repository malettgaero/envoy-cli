"""Tests for envoy.scoper."""
import pytest
from envoy.scoper import scope_env, ScopeResult


@pytest.fixture()
def base_env():
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "APP_NAME": "myapp",
        "APP_ENV": "production",
        "SECRET_KEY": "abc123",
    }


def test_scope_returns_scope_result(base_env):
    result = scope_env(base_env, ["DB_"])
    assert isinstance(result, ScopeResult)


def test_single_prefix_filters_correctly(base_env):
    result = scope_env(base_env, ["DB_"])
    assert set(result.env.keys()) == {"DB_HOST", "DB_PORT"}


def test_multiple_prefixes_combined(base_env):
    result = scope_env(base_env, ["DB_", "APP_"])
    assert set(result.env.keys()) == {"DB_HOST", "DB_PORT", "APP_NAME", "APP_ENV"}


def test_excluded_count_is_correct(base_env):
    result = scope_env(base_env, ["DB_"])
    assert result.excluded_count == 3


def test_matched_count_is_correct(base_env):
    result = scope_env(base_env, ["DB_"])
    assert result.matched_count == 2


def test_strip_prefix_removes_prefix(base_env):
    result = scope_env(base_env, ["DB_"], strip_prefix=True)
    assert set(result.env.keys()) == {"HOST", "PORT"}
    assert result.env["HOST"] == "localhost"


def test_strip_prefix_preserves_values(base_env):
    result = scope_env(base_env, ["APP_"], strip_prefix=True)
    assert result.env["NAME"] == "myapp"
    assert result.env["ENV"] == "production"


def test_empty_prefixes_returns_all_keys(base_env):
    result = scope_env(base_env, [])
    assert result.env == base_env
    assert result.excluded_count == 0


def test_no_match_returns_empty_env(base_env):
    result = scope_env(base_env, ["NOPE_"])
    assert result.env == {}
    assert result.excluded_count == len(base_env)


def test_case_insensitive_match(base_env):
    result = scope_env(base_env, ["db_"], case_sensitive=False)
    assert set(result.env.keys()) == {"DB_HOST", "DB_PORT"}


def test_case_sensitive_no_match(base_env):
    result = scope_env(base_env, ["db_"], case_sensitive=True)
    assert result.env == {}


def test_scope_entry_scope_field_set(base_env):
    result = scope_env(base_env, ["DB_"])
    for entry in result.entries:
        assert entry.scope == "DB_"


def test_scope_entry_to_dict(base_env):
    result = scope_env(base_env, ["DB_"])
    d = result.entries[0].to_dict()
    assert "key" in d and "value" in d and "scope" in d


def test_summary_string(base_env):
    result = scope_env(base_env, ["DB_"])
    s = result.summary()
    assert "2 key(s) matched" in s
    assert "3 excluded" in s


def test_empty_env_returns_empty_result():
    result = scope_env({}, ["DB_"])
    assert result.env == {}
    assert result.excluded_count == 0
    assert result.matched_count == 0
