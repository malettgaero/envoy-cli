"""Tests for envoy.patcher."""

from pathlib import Path

import pytest

from envoy.parser import parse_env_file
from envoy.patcher import patch_env


@pytest.fixture()
def tmp_env(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("APP=hello\nDEBUG=false\nPORT=8080\n")
    return p


# ---------------------------------------------------------------------------
# Basic update
# ---------------------------------------------------------------------------

def test_patch_updates_existing_key(tmp_env: Path) -> None:
    result = patch_env(tmp_env, {"APP": "world"})
    assert result.success
    assert "APP" in result.updated
    assert parse_env_file(tmp_env)["APP"] == "world"


def test_patch_unchanged_key_not_in_updated(tmp_env: Path) -> None:
    result = patch_env(tmp_env, {"APP": "hello"})  # same value
    assert result.success
    assert "APP" not in result.updated


def test_patch_multiple_keys(tmp_env: Path) -> None:
    result = patch_env(tmp_env, {"APP": "new", "PORT": "9090"})
    assert result.success
    assert len(result.updated) == 2
    env = parse_env_file(tmp_env)
    assert env["PORT"] == "9090"


# ---------------------------------------------------------------------------
# add_missing behaviour
# ---------------------------------------------------------------------------

def test_patch_adds_missing_key_by_default(tmp_env: Path) -> None:
    result = patch_env(tmp_env, {"NEW_KEY": "123"})
    assert result.success
    assert "NEW_KEY" in result.added
    assert parse_env_file(tmp_env)["NEW_KEY"] == "123"


def test_patch_skips_missing_key_when_add_missing_false(tmp_env: Path) -> None:
    result = patch_env(tmp_env, {"GHOST": "val"}, add_missing=False)
    assert result.success
    assert "GHOST" in result.skipped
    assert "GHOST" not in parse_env_file(tmp_env)


def test_patch_strict_errors_on_missing_key(tmp_env: Path) -> None:
    result = patch_env(tmp_env, {"GHOST": "val"}, strict=True)
    assert not result.success
    assert any("GHOST" in e for e in result.errors)


# ---------------------------------------------------------------------------
# dry_run
# ---------------------------------------------------------------------------

def test_patch_dry_run_does_not_write(tmp_env: Path) -> None:
    original = tmp_env.read_text()
    result = patch_env(tmp_env, {"APP": "changed"}, dry_run=True)
    assert result.success
    assert "APP" in result.updated
    assert tmp_env.read_text() == original  # file untouched


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_patch_missing_file_returns_error(tmp_path: Path) -> None:
    result = patch_env(tmp_path / "nonexistent.env", {"KEY": "val"})
    assert not result.success
    assert result.errors


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def test_summary_reflects_changes(tmp_env: Path) -> None:
    result = patch_env(tmp_env, {"APP": "x", "BRAND_NEW": "y"})
    s = result.summary()
    assert "updated" in s
    assert "added" in s
