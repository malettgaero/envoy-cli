"""Tests for envoy.counter."""
import pytest
from envoy.counter import count_env, CountResult, CountEntry


@pytest.fixture
def base_env():
    return {
        "APP_NAME": "myapp",
        "APP_VERSION": "1.0",
        "DB_PASSWORD": "s3cr3t",
        "API_KEY": "abc123",
        "DEBUG": "",
        "LOG_LEVEL": "info",
    }


def test_count_returns_count_result(base_env):
    result = count_env(base_env)
    assert isinstance(result, CountResult)


def test_total_matches_env_size(base_env):
    result = count_env(base_env)
    assert result.total == len(base_env)


def test_secret_keys_detected(base_env):
    result = count_env(base_env)
    assert result.count_for("secret") == 2


def test_empty_key_detected(base_env):
    result = count_env(base_env)
    assert result.count_for("empty") == 1


def test_plain_keys_counted(base_env):
    result = count_env(base_env)
    assert result.count_for("plain") == 3


def test_entries_sorted_by_category(base_env):
    result = count_env(base_env)
    cats = [e.category for e in result.entries]
    assert cats == sorted(cats)


def test_keys_sorted_within_category(base_env):
    result = count_env(base_env)
    for entry in result.entries:
        assert entry.keys == sorted(entry.keys)


def test_empty_env_returns_zero_total():
    result = count_env({})
    assert result.total == 0
    assert result.entries == []


def test_count_for_missing_category(base_env):
    result = count_env(base_env)
    assert result.count_for("nonexistent") == 0


def test_summary_contains_total(base_env):
    result = count_env(base_env)
    assert "Total keys: 6" in result.summary()


def test_summary_contains_categories(base_env):
    result = count_env(base_env)
    summary = result.summary()
    assert "secret" in summary
    assert "empty" in summary
    assert "plain" in summary


def test_to_dict_on_entry(base_env):
    result = count_env(base_env)
    for entry in result.entries:
        d = entry.to_dict()
        assert "category" in d
        assert "count" in d
        assert "keys" in d


def test_all_plain_env():
    env = {"FOO": "bar", "BAZ": "qux"}
    result = count_env(env)
    assert result.count_for("plain") == 2
    assert result.count_for("secret") == 0
    assert result.count_for("empty") == 0
