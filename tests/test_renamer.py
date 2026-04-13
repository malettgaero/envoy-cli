"""Tests for envoy.renamer."""
import pytest
from envoy.renamer import rename_keys, RenameResult


def _env(**kwargs) -> dict:
    return dict(kwargs)


def test_rename_single_key():
    env = _env(OLD_KEY="value")
    result = rename_keys(env, {"OLD_KEY": "NEW_KEY"})
    assert "NEW_KEY" in result.env
    assert "OLD_KEY" not in result.env
    assert result.env["NEW_KEY"] == "value"


def test_rename_preserves_other_keys():
    env = _env(KEEP="yes", OLD="val")
    result = rename_keys(env, {"OLD": "NEW"})
    assert result.env["KEEP"] == "yes"
    assert "OLD" not in result.env


def test_rename_multiple_keys():
    env = _env(A="1", B="2", C="3")
    result = rename_keys(env, {"A": "X", "B": "Y"})
    assert result.env == {"X": "1", "Y": "2", "C": "3"}
    assert result.renamed_count == 2


def test_missing_source_key_is_skipped():
    env = _env(EXISTING="v")
    result = rename_keys(env, {"MISSING": "TARGET"})
    assert result.skipped_count == 1
    entry = result.entries[0]
    assert entry.skipped
    assert "not found" in entry.skip_reason


def test_destination_exists_skipped_by_default():
    env = _env(OLD="old_val", NEW="existing")
    result = rename_keys(env, {"OLD": "NEW"})
    assert result.skipped_count == 1
    assert result.env["NEW"] == "existing"  # unchanged
    assert result.env["OLD"] == "old_val"   # still present


def test_destination_exists_overwrite_flag():
    env = _env(OLD="new_val", NEW="existing")
    result = rename_keys(env, {"OLD": "NEW"}, overwrite=True)
    assert result.renamed_count == 1
    assert result.env["NEW"] == "new_val"
    assert "OLD" not in result.env


def test_renamed_count_and_skipped_count():
    env = _env(A="1", B="2")
    result = rename_keys(env, {"A": "X", "GHOST": "Y"})
    assert result.renamed_count == 1
    assert result.skipped_count == 1


def test_summary_contains_ok_and_skip():
    env = _env(A="1")
    result = rename_keys(env, {"A": "X", "MISSING": "Z"})
    summary = result.summary()
    assert "OK" in summary
    assert "SKIP" in summary


def test_empty_renames_returns_unchanged_env():
    env = _env(FOO="bar")
    result = rename_keys(env, {})
    assert result.env == env
    assert result.renamed_count == 0


def test_original_env_not_mutated():
    env = _env(OLD="val")
    original = dict(env)
    rename_keys(env, {"OLD": "NEW"})
    assert env == original
