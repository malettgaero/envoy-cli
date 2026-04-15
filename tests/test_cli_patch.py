"""CLI integration tests for the `envoy patch` command."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from envoy.cli_patch import patch_cmd
from envoy.parser import parse_env_file


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def tmp_env(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("APP=hello\nPORT=8080\n")
    return p


def test_patch_updates_value(runner: CliRunner, tmp_env: Path) -> None:
    result = runner.invoke(patch_cmd, [str(tmp_env), "APP=world"])
    assert result.exit_code == 0
    assert "updated" in result.output
    assert parse_env_file(tmp_env)["APP"] == "world"


def test_patch_adds_new_key(runner: CliRunner, tmp_env: Path) -> None:
    result = runner.invoke(patch_cmd, [str(tmp_env), "NEW=1"])
    assert result.exit_code == 0
    assert "added" in result.output
    assert parse_env_file(tmp_env)["NEW"] == "1"


def test_patch_no_add_skips_missing(runner: CliRunner, tmp_env: Path) -> None:
    result = runner.invoke(patch_cmd, [str(tmp_env), "--no-add", "GHOST=x"])
    assert result.exit_code == 0
    assert "skipped" in result.output
    assert "GHOST" not in parse_env_file(tmp_env)


def test_patch_strict_exits_nonzero_for_missing(runner: CliRunner, tmp_env: Path) -> None:
    result = runner.invoke(patch_cmd, [str(tmp_env), "--strict", "GHOST=x"])
    assert result.exit_code != 0
    assert "error" in result.output.lower()


def test_patch_dry_run_does_not_write(runner: CliRunner, tmp_env: Path) -> None:
    original = tmp_env.read_text()
    result = runner.invoke(patch_cmd, [str(tmp_env), "--dry-run", "APP=changed"])
    assert result.exit_code == 0
    assert "dry-run" in result.output
    assert tmp_env.read_text() == original


def test_patch_invalid_assignment_exits_nonzero(runner: CliRunner, tmp_env: Path) -> None:
    result = runner.invoke(patch_cmd, [str(tmp_env), "NOEQUALSIGN"])
    assert result.exit_code != 0


def test_patch_multiple_assignments(runner: CliRunner, tmp_env: Path) -> None:
    result = runner.invoke(patch_cmd, [str(tmp_env), "APP=a", "PORT=9000"])
    assert result.exit_code == 0
    env = parse_env_file(tmp_env)
    assert env["APP"] == "a"
    assert env["PORT"] == "9000"


def test_patch_missing_file_exits_nonzero(runner: CliRunner, tmp_path: Path) -> None:
    """Patching a file that does not exist should exit with a non-zero status."""
    missing = tmp_path / "nonexistent.env"
    result = runner.invoke(patch_cmd, [str(missing), "APP=value"])
    assert result.exit_code != 0
    assert "error" in result.output.lower() or "no such" in result.output.lower()
