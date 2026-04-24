"""Tests for envoy.anchorer."""
import pytest
from envoy.anchorer import anchor_env, AnchorEntry, AnchorResult


@pytest.fixture
def base_env():
    return {
        "APP_NAME": "myapp",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "SECRET_KEY": "abc123",
        "LOG_LEVEL": "info",
    }


def test_anchor_returns_anchor_result(base_env):
    result = anchor_env(base_env)
    assert isinstance(result, AnchorResult)


def test_all_keys_present(base_env):
    result = anchor_env(base_env)
    assert set(result.env.keys()) == set(base_env.keys())


def test_top_keys_come_first(base_env):
    result = anchor_env(base_env, top_keys=["SECRET_KEY", "APP_NAME"])
    order = result.order
    assert order.index("SECRET_KEY") < order.index("DB_HOST")
    assert order.index("APP_NAME") < order.index("DB_HOST")


def test_bottom_keys_come_last(base_env):
    result = anchor_env(base_env, bottom_keys=["LOG_LEVEL"])
    order = result.order
    assert order[-1] == "LOG_LEVEL"


def test_top_and_bottom_combined(base_env):
    result = anchor_env(base_env, top_keys=["APP_NAME"], bottom_keys=["LOG_LEVEL"])
    order = result.order
    assert order[0] == "APP_NAME"
    assert order[-1] == "LOG_LEVEL"


def test_position_field_set_correctly(base_env):
    result = anchor_env(base_env, top_keys=["APP_NAME"], bottom_keys=["LOG_LEVEL"])
    pos = {e.key: e.position for e in result.entries}
    assert pos["APP_NAME"] == "top"
    assert pos["LOG_LEVEL"] == "bottom"
    assert pos["DB_HOST"] == "free"


def test_group_position_assigned(base_env):
    result = anchor_env(base_env, groups={"database": ["DB_HOST", "DB_PORT"]})
    pos = {e.key: e.position for e in result.entries}
    assert pos["DB_HOST"] == "group"
    assert pos["DB_PORT"] == "group"


def test_group_label_stored(base_env):
    result = anchor_env(base_env, groups={"database": ["DB_HOST", "DB_PORT"]})
    groups = {e.key: e.group for e in result.entries}
    assert groups["DB_HOST"] == "database"
    assert groups["APP_NAME"] is None


def test_changed_false_when_no_reorder():
    env = {"A": "1", "B": "2"}
    result = anchor_env(env)
    assert not result.changed


def test_changed_true_when_reordered():
    env = {"A": "1", "B": "2", "C": "3"}
    result = anchor_env(env, top_keys=["C"])
    assert result.changed


def test_missing_top_key_ignored():
    env = {"A": "1", "B": "2"}
    result = anchor_env(env, top_keys=["MISSING"])
    assert "MISSING" not in result.env
    assert set(result.env.keys()) == {"A", "B"}


def test_summary_contains_counts(base_env):
    result = anchor_env(base_env, top_keys=["APP_NAME"], bottom_keys=["LOG_LEVEL"])
    s = result.summary()
    assert "1 anchored top" in s
    assert "1 anchored bottom" in s


def test_to_dict_on_entry(base_env):
    result = anchor_env(base_env, top_keys=["APP_NAME"])
    entry = next(e for e in result.entries if e.key == "APP_NAME")
    d = entry.to_dict()
    assert d["key"] == "APP_NAME"
    assert d["position"] == "top"
    assert "value" in d
    assert "group" in d


def test_empty_env_returns_empty_result():
    result = anchor_env({})
    assert result.entries == []
    assert result.order == []
    assert not result.changed
