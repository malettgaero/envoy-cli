"""Integration tests for the `envoy rename` CLI command."""
from pathlib import Path

import pytest
from click.testing import CliRunner

from envoy.cli_rename import rename_cmd
from envoy.parser import parse_env_file


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def tmp_env(tmp_path):
    p = tmp_path / ".env"
    p.write_text("OLD_KEY=hello\nKEEP=world\n")
    return p


def test_rename_updates_file(runner, tmp_env):
    result = runner.invoke(rename_cmd, [str(tmp_env), "OLD_KEY=NEW_KEY"])
    assert result.exit_code == 0
    env = parse_env_file(tmp_env)
    assert "NEW_KEY" in env
    assert "OLD_KEY" not in env
    assert env["NEW_KEY"] == "hello"


def test_rename_preserves_other_keys(runner, tmp_env):
    runner.invoke(rename_cmd, [str(tmp_env), "OLD_KEY=NEW_KEY"])
    env = parse_env_file(tmp_env)
    assert env["KEEP"] == "world"


def test_dry_run_does_not_write(runner, tmp_env):
    before = tmp_env.read_text()
    result = runner.invoke(rename_cmd, [str(tmp_env), "OLD_KEY=NEW_KEY", "--dry-run"])
    assert result.exit_code == 0
    assert tmp_env.read_text() == before
    assert "dry-run" in result.output


def test_invalid_spec_exits_nonzero(runner, tmp_env):
    result = runner.invoke(rename_cmd, [str(tmp_env), "BADSPEC"])
    assert result.exit_code != 0


def test_missing_source_key_skipped(runner, tmp_env):
    result = runner.invoke(rename_cmd, [str(tmp_env), "GHOST=TARGET"])
    assert result.exit_code == 0
    assert "SKIP" in result.output
    env = parse_env_file(tmp_env)
    assert "TARGET" not in env


def test_output_flag_writes_to_different_file(runner, tmp_env, tmp_path):
    out = tmp_path / "out.env"
    result = runner.invoke(rename_cmd, [str(tmp_env), "OLD_KEY=NEW_KEY", "--out", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    env = parse_env_file(out)
    assert "NEW_KEY" in env
    # original file should be unchanged
    original = parse_env_file(tmp_env)
    assert "OLD_KEY" in original


def test_overwrite_flag_replaces_existing_key(runner, tmp_path):
    p = tmp_path / ".env"
    p.write_text("SRC=new_val\nDST=old_val\n")
    result = runner.invoke(rename_cmd, [str(p), "SRC=DST", "--overwrite"])
    assert result.exit_code == 0
    env = parse_env_file(p)
    assert env["DST"] == "new_val"
    assert "SRC" not in env
