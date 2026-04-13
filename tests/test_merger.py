"""Tests for envoy.merger module."""

import pytest
from envoy.merger import (
    MergeConflict,
    MergeError,
    MergeResult,
    Strategy,
    merge_envs,
)


def test_merge_empty_list_returns_empty():
    result = merge_envs([])
    assert result.merged == {}
    assert result.conflicts == []
    assert result.sources_used == []


def test_merge_single_source():
    result = merge_envs([("base", {"A": "1", "B": "2"})])
    assert result.merged == {"A": "1", "B": "2"}
    assert not result.has_conflicts
    assert result.sources_used == ["base"]


def test_merge_no_conflicts():
    a = {"HOST": "localhost", "PORT": "5432"}
    b = {"DEBUG": "true", "LOG_LEVEL": "info"}
    result = merge_envs([("a", a), ("b", b)])
    assert result.merged == {"HOST": "localhost", "PORT": "5432", "DEBUG": "true", "LOG_LEVEL": "info"}
    assert not result.has_conflicts


def test_merge_last_wins_strategy():
    a = {"KEY": "original"}
    b = {"KEY": "override"}
    result = merge_envs([("a", a), ("b", b)], strategy=Strategy.LAST_WINS)
    assert result.merged["KEY"] == "override"
    assert result.has_conflicts
    assert result.conflicts[0].key == "KEY"


def test_merge_first_wins_strategy():
    a = {"KEY": "original"}
    b = {"KEY": "override"}
    result = merge_envs([("a", a), ("b", b)], strategy=Strategy.FIRST_WINS)
    assert result.merged["KEY"] == "original"
    assert result.has_conflicts


def test_merge_strict_strategy_raises_on_conflict():
    a = {"KEY": "v1"}
    b = {"KEY": "v2"}
    with pytest.raises(MergeError, match="Conflict on key 'KEY'"):
        merge_envs([("a", a), ("b", b)], strategy=Strategy.STRICT)


def test_merge_strict_no_conflict_succeeds():
    a = {"A": "1"}
    b = {"B": "2"}
    result = merge_envs([("a", a), ("b", b)], strategy=Strategy.STRICT)
    assert result.merged == {"A": "1", "B": "2"}
    assert not result.has_conflicts


def test_merge_identical_values_not_a_conflict():
    a = {"KEY": "same"}
    b = {"KEY": "same"}
    result = merge_envs([("a", a), ("b", b)])
    assert result.merged["KEY"] == "same"
    assert not result.has_conflicts


def test_merge_result_summary_no_conflicts():
    result = merge_envs([("a", {"X": "1"}), ("b", {"Y": "2"})])
    summary = result.summary()
    assert "2 source(s)" in summary
    assert "2 key(s)" in summary
    assert "conflict" not in summary


def test_merge_result_summary_with_conflicts():
    result = merge_envs([("a", {"K": "v1"}), ("b", {"K": "v2"})])
    summary = result.summary()
    assert "1 conflict(s)" in summary
    assert "K" in summary


def test_merge_conflict_str():
    c = MergeConflict(key="DB_URL", values=[("base", "postgres://a"), ("prod", "postgres://b")])
    s = str(c)
    assert "DB_URL" in s
    assert "base" in s
    assert "prod" in s
