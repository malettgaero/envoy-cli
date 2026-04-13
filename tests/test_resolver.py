"""Tests for envoy.resolver."""

import pytest
from envoy.resolver import resolve_envs, ResolveResult


BASE = {"APP": "myapp", "PORT": "8080", "DEBUG": "false"}
OVERRIDE = {"PORT": "9090", "LOG_LEVEL": "info"}
EXTRA = {"PORT": "7070", "REGION": "us-east-1"}


def test_single_source_resolves_all_keys():
    result = resolve_envs([("base", BASE)])
    assert result.env == BASE
    assert len(result.shadowed) == 0


def test_last_wins_overrides_earlier_source():
    result = resolve_envs([("base", BASE), ("override", OVERRIDE)])
    assert result.env["PORT"] == "9090"
    assert result.env["APP"] == "myapp"
    assert result.env["LOG_LEVEL"] == "info"


def test_last_wins_records_shadowed_entry():
    result = resolve_envs([("base", BASE), ("override", OVERRIDE)])
    shadowed_keys = [e.key for e in result.shadowed]
    assert "PORT" in shadowed_keys


def test_shadowed_entry_has_correct_source_and_overrider():
    result = resolve_envs([("base", BASE), ("override", OVERRIDE)])
    entry = next(e for e in result.shadowed if e.key == "PORT")
    assert entry.source == "base"
    assert entry.overridden_by == "override"
    assert entry.value == "8080"


def test_first_wins_keeps_earliest_definition():
    result = resolve_envs([("base", BASE), ("override", OVERRIDE)], last_wins=False)
    assert result.env["PORT"] == "8080"


def test_first_wins_still_merges_unique_keys():
    result = resolve_envs([("base", BASE), ("override", OVERRIDE)], last_wins=False)
    assert "LOG_LEVEL" in result.env


def test_three_sources_last_wins():
    result = resolve_envs([("base", BASE), ("override", OVERRIDE), ("extra", EXTRA)])
    assert result.env["PORT"] == "7070"
    assert result.env["REGION"] == "us-east-1"
    assert len([e for e in result.shadowed if e.key == "PORT"]) == 2


def test_empty_sources_returns_empty():
    result = resolve_envs([])
    assert result.env == {}
    assert result.shadowed == []


def test_no_overlap_no_shadowed():
    a = {"A": "1"}
    b = {"B": "2"}
    result = resolve_envs([("a", a), ("b", b)])
    assert len(result.shadowed) == 0
    assert result.env == {"A": "1", "B": "2"}


def test_summary_contains_resolved_count():
    result = resolve_envs([("base", BASE), ("override", OVERRIDE)])
    summary = result.summary()
    assert "Resolved" in summary
    assert str(len(result.resolved)) in summary


def test_summary_mentions_shadowed_keys():
    result = resolve_envs([("base", BASE), ("override", OVERRIDE)])
    summary = result.summary()
    assert "PORT" in summary
    assert "shadowed" in summary


def test_resolved_entry_to_dict():
    result = resolve_envs([("base", {"KEY": "val"})])
    d = result.resolved["KEY"].to_dict()
    assert d["key"] == "KEY"
    assert d["value"] == "val"
    assert d["source"] == "base"
    assert d["overridden_by"] is None
