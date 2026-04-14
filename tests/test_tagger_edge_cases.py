"""Edge-case tests for envoy.tagger."""
from envoy.tagger import tag_env


def test_empty_env_returns_empty_result():
    result = tag_env({}, {})
    assert result.entries == []
    assert result.all_tags() == set()


def test_empty_tag_map_all_keys_untagged():
    env = {"FOO": "1", "BAR": "2"}
    result = tag_env(env, {})
    for entry in result.entries:
        assert entry.tags == set()


def test_multiple_tags_on_same_key():
    env = {"SECRET_KEY": "xyz"}
    tag_map = {"SECRET_KEY": ["secret", "critical", "do-not-log"]}
    result = tag_env(env, tag_map)
    assert result.tags_for_key("SECRET_KEY") == {"secret", "critical", "do-not-log"}


def test_same_tag_on_multiple_keys():
    env = {"DB_PASS": "x", "API_SECRET": "y", "TOKEN": "z"}
    tag_map = {k: ["sensitive"] for k in env}
    result = tag_env(env, tag_map)
    assert set(result.keys_for_tag("sensitive")) == set(env.keys())


def test_tags_for_missing_key_returns_empty():
    result = tag_env({"A": "1"}, {})
    assert result.tags_for_key("DOES_NOT_EXIST") == set()


def test_all_tags_empty_when_no_tags_applied():
    env = {"X": "1", "Y": "2"}
    result = tag_env(env, {})
    assert result.all_tags() == set()


def test_summary_zero_tagged():
    env = {"A": "1", "B": "2"}
    result = tag_env(env, {})
    assert result.summary().startswith("0/2")
