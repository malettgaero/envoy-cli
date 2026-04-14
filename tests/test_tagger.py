"""Tests for envoy.tagger."""
import pytest
from envoy.tagger import TagEntry, TagResult, tag_env


@pytest.fixture()
def base_env():
    return {
        "APP_NAME": "myapp",
        "DB_HOST": "localhost",
        "DB_PASSWORD": "secret",
        "API_KEY": "abc123",
        "DEBUG": "true",
    }


def test_tag_env_returns_tag_result(base_env):
    result = tag_env(base_env, {})
    assert isinstance(result, TagResult)


def test_all_keys_present_without_tag_map(base_env):
    result = tag_env(base_env, {})
    assert {e.key for e in result.entries} == set(base_env)


def test_keys_sorted_alphabetically(base_env):
    result = tag_env(base_env, {})
    keys = [e.key for e in result.entries]
    assert keys == sorted(keys)


def test_tags_applied_correctly(base_env):
    tag_map = {"DB_PASSWORD": ["secret"], "API_KEY": ["secret", "external"]}
    result = tag_env(base_env, tag_map)
    assert result.tags_for_key("DB_PASSWORD") == {"secret"}
    assert result.tags_for_key("API_KEY") == {"secret", "external"}


def test_untagged_key_has_empty_set(base_env):
    result = tag_env(base_env, {"DB_PASSWORD": ["secret"]})
    assert result.tags_for_key("APP_NAME") == set()


def test_keys_for_tag_returns_correct_keys(base_env):
    tag_map = {"DB_PASSWORD": ["secret"], "API_KEY": ["secret"]}
    result = tag_env(base_env, tag_map)
    assert set(result.keys_for_tag("secret")) == {"DB_PASSWORD", "API_KEY"}


def test_keys_for_unknown_tag_returns_empty(base_env):
    result = tag_env(base_env, {})
    assert result.keys_for_tag("nonexistent") == []


def test_all_tags_collected(base_env):
    tag_map = {
        "DB_PASSWORD": ["secret"],
        "API_KEY": ["secret", "external"],
        "DEBUG": ["feature-flag"],
    }
    result = tag_env(base_env, tag_map)
    assert result.all_tags() == {"secret", "external", "feature-flag"}


def test_tag_map_key_not_in_env_is_ignored():
    env = {"APP_NAME": "x"}
    tag_map = {"MISSING_KEY": ["orphan"]}
    result = tag_env(env, tag_map)
    assert result.keys_for_tag("orphan") == []


def test_summary_format(base_env):
    tag_map = {"DB_PASSWORD": ["secret"], "API_KEY": ["external"]}
    result = tag_env(base_env, tag_map)
    summary = result.summary()
    assert "2/5" in summary
    assert "2 distinct tag" in summary


def test_to_dict_contains_sorted_tags():
    entry = TagEntry(key="FOO", tags={"z-tag", "a-tag"})
    d = entry.to_dict()
    assert d["key"] == "FOO"
    assert d["tags"] == ["a-tag", "z-tag"]
