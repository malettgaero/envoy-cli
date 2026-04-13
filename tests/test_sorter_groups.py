"""Edge-case tests for group-based sorting in envoy.sorter."""
import pytest
from envoy.sorter import sort_env


def test_group_key_missing_from_env_is_skipped():
    env = {"APPLE": "1", "BANANA": "2"}
    result = sort_env(env, groups=[["MISSING_KEY"]])
    keys = list(result.sorted_env.keys())
    assert "MISSING_KEY" not in keys
    assert set(keys) == {"APPLE", "BANANA"}


def test_group_key_not_duplicated():
    env = {"A": "1", "B": "2", "C": "3"}
    result = sort_env(env, groups=[["A"], ["A"]])
    keys = list(result.sorted_env.keys())
    assert keys.count("A") == 1


def test_multiple_keys_in_single_group_preserves_group_order():
    env = {"Z": "1", "A": "2", "FIRST": "0", "SECOND": "00", "THIRD": "000"}
    result = sort_env(env, groups=[["FIRST", "SECOND", "THIRD"]])
    keys = list(result.sorted_env.keys())
    assert keys[:3] == ["FIRST", "SECOND", "THIRD"]


def test_remaining_keys_sorted_after_groups():
    env = {"Z": "1", "A": "2", "PIN": "0"}
    result = sort_env(env, groups=[["PIN"]])
    remaining = list(result.sorted_env.keys())[1:]
    assert remaining == sorted(remaining, key=lambda k: k.lower())


def test_order_attribute_matches_sorted_env_keys():
    env = {"Z": "1", "A": "2", "M": "3"}
    result = sort_env(env)
    assert result.order == list(result.sorted_env.keys())


def test_single_key_env_unchanged():
    env = {"ONLY": "value"}
    result = sort_env(env)
    assert result.sorted_env == {"ONLY": "value"}
    assert result.changed is False
