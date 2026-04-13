"""End-to-end integration tests: patch_cmd wired through a Click group."""

from pathlib import Path

import pytest
from click.testing import CliRunner
import click

from envoy.cli_patch import patch_cmd
from envoy.parser import parse_env_file


@click.group()
def cli() -> None:
    pass


cli.add_command(patch_cmd)


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / "prod.env"
    p.write_text("DB_HOST=localhost\nDB_PORT=5432\nSECRET=old\n")
    return p


def test_full_patch_roundtrip(runner: CliRunner, env_file: Path) -> None:
    """Patch multiple keys and verify the file contents are correct."""
    result = runner.invoke(cli, ["patch", str(env_file), "DB_HOST=db.prod", "SECRET=new"])
    assert result.exit_code == 0, result.output
    env = parse_env_file(env_file)
    assert env["DB_HOST"] == "db.prod"
    assert env["SECRET"] == "new"
    assert env["DB_PORT"] == "5432"  # untouched


def test_patch_preserves_unrelated_keys(runner: CliRunner, env_file: Path) -> None:
    result = runner.invoke(cli, ["patch", str(env_file), "SECRET=changed"])
    assert result.exit_code == 0
    env = parse_env_file(env_file)
    assert env["DB_HOST"] == "localhost"
    assert env["DB_PORT"] == "5432"


def test_patch_add_and_update_together(runner: CliRunner, env_file: Path) -> None:
    result = runner.invoke(
        cli, ["patch", str(env_file), "DB_PORT=5433", "NEW_KEY=hello"]
    )
    assert result.exit_code == 0
    env = parse_env_file(env_file)
    assert env["DB_PORT"] == "5433"
    assert env["NEW_KEY"] == "hello"


def test_patch_summary_output(runner: CliRunner, env_file: Path) -> None:
    result = runner.invoke(cli, ["patch", str(env_file), "DB_PORT=9999", "EXTRA=yes"])
    assert result.exit_code == 0
    assert "updated" in result.output
    assert "added" in result.output
