"""Tests for envoy.deduplicator."""
import pytest
from envoy.deduplicator import DeduplicateEntry, DeduplicateResult, KeepStrategy, deduplicate_env


def _pairs(*items):
    """Build a list of (key, value) tuples from alternating args."""
    it = iter(items)
    return list(zip(it, it))


# ---------------------------------------------------------------------------
# Basic behaviour
# ---------------------------------------------------------------------------

def test_no_duplicates_returns_empty_result():
    pairs = _pairs("A", "1", "B", "2", "C", "3")
    result = deduplicate_env(pairs)
    assert not result.has_duplicates
    assert result.duplicate_count == 0
    assert result.clean_env == {"A": "1", "B": "2", "C": "3"}


def test_single_duplicate_detected():
    pairs = _pairs("KEY", "first", "OTHER", "x", "KEY", "second")
    result = deduplicate_env(pairs)
    assert result.has_duplicates
    assert result.duplicate_count == 1
    assert result.entries[0].key == "KEY"
    assert result.entries[0].occurrences == 2


def test_first_wins_strategy_keeps_first_value():
    pairs = _pairs("DB", "dev", "DB", "prod", "DB", "staging")
    result = deduplicate_env(pairs, strategy=KeepStrategy.FIRST)
    assert result.clean_env["DB"] == "dev"
    entry = result.entries[0]
    assert entry.kept_value == "dev"
    assert entry.dropped_values == ["prod", "staging"]


def test_last_wins_strategy_keeps_last_value():
    pairs = _pairs("DB", "dev", "DB", "prod", "DB", "staging")
    result = deduplicate_env(pairs, strategy=KeepStrategy.LAST)
    assert result.clean_env["DB"] == "staging"
    entry = result.entries[0]
    assert entry.kept_value == "staging"
    assert entry.dropped_values == ["dev", "prod"]


def test_multiple_duplicate_keys():
    pairs = _pairs("X", "1", "Y", "a", "X", "2", "Y", "b")
    result = deduplicate_env(pairs)
    assert result.duplicate_count == 2
    keys = {e.key for e in result.entries}
    assert keys == {"X", "Y"}


def test_clean_env_preserves_insertion_order():
    pairs = _pairs("Z", "last", "A", "first", "M", "mid", "A", "dup")
    result = deduplicate_env(pairs)
    assert list(result.clean_env.keys()) == ["Z", "A", "M"]


def test_empty_pairs_returns_empty_result():
    result = deduplicate_env([])
    assert not result.has_duplicates
    assert result.clean_env == {}


# ---------------------------------------------------------------------------
# to_dict / summary
# ---------------------------------------------------------------------------

def test_entry_to_dict_has_expected_keys():
    pairs = _pairs("SECRET", "old", "SECRET", "new")
    result = deduplicate_env(pairs, strategy=KeepStrategy.LAST)
    d = result.entries[0].to_dict()
    assert set(d.keys()) == {"key", "kept_value", "dropped_values", "occurrences"}
    assert d["key"] == "SECRET"
    assert d["occurrences"] == 2


def test_summary_no_duplicates():
    result = deduplicate_env(_pairs("A", "1"))
    assert result.summary() == "No duplicate keys found."


def test_summary_with_duplicates_mentions_key():
    pairs = _pairs("FOO", "bar", "FOO", "baz")
    result = deduplicate_env(pairs)
    summary = result.summary()
    assert "FOO" in summary
    assert "1 duplicate key(s) removed" in summary
