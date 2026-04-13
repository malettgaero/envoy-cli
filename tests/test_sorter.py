"""Tests for envoy.sorter."""
import pytest
from envoy.sorter import sort_env, SortResult


@pytest.fixture
def base_env():
    return {"ZEBRA": "1", "APPLE": "2", "MANGO": "3", "banana": "4"}


def test_sort_returns_sort_result(base_env):
    result = sort_env(base_env)
    assert isinstance(result, SortResult)


def test_sort_alphabetical_case_insensitive(base_env):
    result = sort_env(base_env)
    keys = list(result.sorted_env.keys())
    assert keys == sorted(keys, key=lambda k: k.lower())


def test_sort_alphabetical_case_sensitive():
    env = {"b": "1", "A": "2", "c": "3"}
    result = sort_env(env, case_sensitive=True)
    keys = list(result.sorted_env.keys())
    assert keys == sorted(keys)


def test_sort_preserves_values(base_env):
    result = sort_env(base_env)
    for k, v in base_env.items():
        assert result.sorted_env[k] == v


def test_changed_flag_when_order_differs(base_env):
    result = sort_env(base_env)
    assert result.changed is True


def test_changed_flag_false_when_already_sorted():
    env = {"APPLE": "1", "BANANA": "2", "CHERRY": "3"}
    result = sort_env(env)
    assert result.changed is False


def test_sort_with_groups_places_group_first():
    env = {"Z": "1", "A": "2", "M": "3", "PRIORITY": "0"}
    result = sort_env(env, groups=[["PRIORITY"]])
    keys = list(result.sorted_env.keys())
    assert keys[0] == "PRIORITY"
    assert keys[1:] == sorted(keys[1:], key=lambda k: k.lower())


def test_sort_with_multiple_groups():
    env = {"Z": "1", "A": "2", "FIRST": "0", "SECOND": "00"}
    result = sort_env(env, groups=[["FIRST"], ["SECOND"]])
    keys = list(result.sorted_env.keys())
    assert keys[0] == "FIRST"
    assert keys[1] == "SECOND"


def test_summary_sorted(base_env):
    result = sort_env(base_env)
    assert "Sorted" in result.summary()


def test_summary_already_sorted():
    env = {"ALPHA": "1", "BETA": "2"}
    result = sort_env(env)
    assert "already" in result.summary()


def test_empty_env_sorts_cleanly():
    result = sort_env({})
    assert result.sorted_env == {}
    assert result.changed is False
