"""Tests for envoy.grouper."""
import pytest
from envoy.grouper import group_env, GroupResult, GroupEntry


@pytest.fixture()
def base_env():
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "AWS_ACCESS_KEY": "AKIA",
        "AWS_SECRET": "secret",
        "APP_NAME": "myapp",
        "DEBUG": "true",
    }


def test_group_env_returns_group_result(base_env):
    result = group_env(base_env)
    assert isinstance(result, GroupResult)


def test_auto_detect_groups_by_prefix(base_env):
    result = group_env(base_env)
    groups = result.groups
    assert "DB" in groups
    assert "AWS" in groups
    assert "APP" in groups


def test_key_without_underscore_is_ungrouped(base_env):
    result = group_env(base_env)
    ungrouped = result.keys_for_prefix("")
    assert "DEBUG" in ungrouped


def test_explicit_prefixes_override_auto_detect(base_env):
    result = group_env(base_env, prefixes=["DB", "AWS"])
    assert "DB_HOST" in result.keys_for_prefix("DB")
    assert "AWS_ACCESS_KEY" in result.keys_for_prefix("AWS")
    # APP_NAME does not match explicit prefixes -> ungrouped
    assert "APP_NAME" in result.keys_for_prefix("")


def test_keys_sorted_alphabetically(base_env):
    result = group_env(base_env)
    db_keys = result.keys_for_prefix("DB")
    assert db_keys == sorted(db_keys)


def test_prefix_for_key_returns_correct_prefix(base_env):
    result = group_env(base_env)
    assert result.prefix_for_key("DB_HOST") == "DB"
    assert result.prefix_for_key("AWS_SECRET") == "AWS"


def test_prefix_for_missing_key_returns_none(base_env):
    result = group_env(base_env)
    assert result.prefix_for_key("NONEXISTENT") is None


def test_summary_contains_all_groups(base_env):
    result = group_env(base_env)
    summary = result.summary()
    assert "DB" in summary
    assert "AWS" in summary


def test_empty_env_returns_empty_result():
    result = group_env({})
    assert result.entries == []
    assert result.summary() == "no keys"


def test_auto_detect_false_all_ungrouped(base_env):
    result = group_env(base_env, auto_detect=False)
    for entry in result.entries:
        assert entry.prefix == ""


def test_entry_to_dict(base_env):
    result = group_env(base_env)
    entry = next(e for e in result.entries if e.key == "DB_HOST")
    d = entry.to_dict()
    assert d["key"] == "DB_HOST"
    assert d["prefix"] == "DB"
    assert "value" in d
