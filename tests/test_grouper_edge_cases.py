"""Edge-case tests for envoy.grouper."""
from envoy.grouper import group_env


def test_single_key_no_underscore():
    result = group_env({"PLAIN": "value"})
    assert result.keys_for_prefix("") == ["PLAIN"]


def test_key_with_multiple_underscores_uses_first_segment():
    result = group_env({"A_B_C": "1"})
    assert result.prefix_for_key("A_B_C") == "A"


def test_explicit_prefix_case_insensitive():
    env = {"db_host": "localhost", "db_port": "5432"}
    result = group_env(env, prefixes=["DB"])
    # lowercase keys: prefix detection compares uppercased key prefix
    matched = result.keys_for_prefix("DB")
    assert "db_host" in matched
    assert "db_port" in matched


def test_groups_property_returns_sorted_prefixes():
    env = {"Z_KEY": "1", "A_KEY": "2", "M_KEY": "3"}
    result = group_env(env)
    prefixes = list(result.groups.keys())
    assert prefixes == sorted(prefixes)


def test_all_keys_present_in_entries():
    env = {"X": "1", "Y_A": "2", "Y_B": "3"}
    result = group_env(env)
    keys = {e.key for e in result.entries}
    assert keys == set(env.keys())
