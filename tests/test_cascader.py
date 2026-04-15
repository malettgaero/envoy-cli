"""Tests for envoy.cascader."""
import pytest
from envoy.cascader import cascade_envs, CascadeResult


def _src(label: str, **kv) -> tuple:
    return (label, dict(kv))


def test_empty_sources_returns_empty_result():
    result = cascade_envs([])
    assert result.env == {}
    assert result.override_count == 0


def test_single_source_all_keys_present():
    result = cascade_envs([_src("base", A="1", B="2")])
    assert result.env == {"A": "1", "B": "2"}
    assert result.override_count == 0


def test_later_source_overrides_earlier():
    result = cascade_envs([
        _src("base", DB_HOST="localhost"),
        _src("prod", DB_HOST="prod.db"),
    ])
    assert result.env["DB_HOST"] == "prod.db"


def test_override_count_is_correct():
    result = cascade_envs([
        _src("base", A="1", B="2"),
        _src("local", A="99"),
    ])
    assert result.override_count == 1


def test_shadowed_entry_has_correct_source():
    result = cascade_envs([
        _src("base", X="old"),
        _src("override", X="new"),
    ])
    assert len(result.shadowed) == 1
    s = result.shadowed[0]
    assert s.key == "X"
    assert s.value == "old"
    assert s.source == "base"
    assert s.overridden_by == "override"


def test_unique_keys_from_all_layers_are_kept():
    result = cascade_envs([
        _src("base", A="1"),
        _src("mid", B="2"),
        _src("top", C="3"),
    ])
    assert set(result.env.keys()) == {"A", "B", "C"}


def test_three_layer_cascade_last_wins():
    result = cascade_envs([
        _src("base", KEY="v1"),
        _src("staging", KEY="v2"),
        _src("local", KEY="v3"),
    ])
    assert result.env["KEY"] == "v3"
    assert result.override_count == 2


def test_entries_sorted_alphabetically():
    result = cascade_envs([_src("base", Z="z", A="a", M="m")])
    keys = [e.key for e in result.entries]
    assert keys == sorted(keys)


def test_summary_no_overrides():
    result = cascade_envs([_src("base", A="1")])
    assert "1 key" in result.summary()
    assert "overridden" not in result.summary()


def test_summary_with_overrides():
    result = cascade_envs([
        _src("base", A="1"),
        _src("local", A="2"),
    ])
    assert "overridden" in result.summary()


def test_to_dict_fields():
    result = cascade_envs([
        _src("base", KEY="val"),
        _src("override", KEY="new"),
    ])
    d = result.entries[0].to_dict()
    assert "key" in d and "value" in d and "source" in d and "overridden_by" in d
