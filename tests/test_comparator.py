"""Tests for envoy.comparator."""
import pytest
from envoy.comparator import compare_envs, CompareEntry, CompareResult


ENV_A = {"HOST": "localhost", "PORT": "5432", "DEBUG": "true"}
ENV_B = {"HOST": "prod.example.com", "PORT": "5432", "SECRET": "abc123"}
ENV_C = {"HOST": "staging.example.com", "PORT": "5432", "DEBUG": "false"}


def test_all_keys_collected():
    result = compare_envs({"a": ENV_A, "b": ENV_B})
    assert set(result.all_keys) == {"HOST", "PORT", "DEBUG", "SECRET"}


def test_consistent_key_detected():
    result = compare_envs({"a": ENV_A, "b": ENV_B})
    port_entry = next(e for e in result.entries if e.key == "PORT")
    assert port_entry.is_consistent is True


def test_inconsistent_key_detected():
    result = compare_envs({"a": ENV_A, "b": ENV_B})
    host_entry = next(e for e in result.entries if e.key == "HOST")
    assert host_entry.is_consistent is False
    assert host_entry in result.inconsistent_entries


def test_missing_key_detected():
    result = compare_envs({"a": ENV_A, "b": ENV_B})
    secret_entry = next(e for e in result.entries if e.key == "SECRET")
    assert secret_entry.is_missing_in_some is True
    assert secret_entry.values["a"] is None
    assert secret_entry.values["b"] == "abc123"


def test_keys_sorted_alphabetically():
    result = compare_envs({"a": ENV_A, "b": ENV_B})
    assert result.all_keys == sorted(result.all_keys)


def test_mask_secrets_replaces_values():
    result = compare_envs({"a": ENV_A, "b": ENV_B}, mask_secrets=True)
    for entry in result.entries:
        for name, val in entry.values.items():
            if val is not None:
                assert val == "***"


def test_mask_secrets_keeps_none_for_missing():
    result = compare_envs({"a": ENV_A, "b": ENV_B}, mask_secrets=True)
    secret_entry = next(e for e in result.entries if e.key == "SECRET")
    assert secret_entry.values["a"] is None


def test_three_envs_comparison():
    result = compare_envs({"a": ENV_A, "b": ENV_B, "c": ENV_C})
    assert result.env_names == ["a", "b", "c"]
    debug_entry = next(e for e in result.entries if e.key == "DEBUG")
    assert debug_entry.is_missing_in_some is True  # missing in b
    assert debug_entry.values["b"] is None


def test_summary_output():
    result = compare_envs({"a": ENV_A, "b": ENV_B})
    summary = result.summary()
    assert "Environments compared" in summary
    assert "a" in summary and "b" in summary
    assert "Total keys" in summary


def test_empty_envs_returns_empty_result():
    result = compare_envs({"a": {}, "b": {}})
    assert result.entries == []
    assert result.inconsistent_entries == []


def test_single_env_all_consistent():
    result = compare_envs({"only": ENV_A})
    assert all(e.is_consistent for e in result.entries)
