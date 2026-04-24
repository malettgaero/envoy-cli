"""CLI tests for the stencil command."""
import pytest
from click.testing import CliRunner
from pathlib import Path

from envoy.cli_stencil import stencil_cmd


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def tmp_env(tmp_path):
    p = tmp_path / ".env"
    p.write_text("APP_NAME=myapp\nDB_HOST=localhost\nSECRET_KEY=s3cr3t\n")
    return p


def test_stencil_filters_keys(runner, tmp_env):
    result = runner.invoke(stencil_cmd, [str(tmp_env), "--key", "APP_NAME"])
    assert result.exit_code == 0
    assert "APP_NAME=myapp" in result.output
    assert "DB_HOST" not in result.output


def test_stencil_shows_dropped_keys(runner, tmp_env):
    result = runner.invoke(stencil_cmd, [str(tmp_env), "--key", "APP_NAME"])
    assert "Dropped" in result.output
    assert "DB_HOST" in result.output or "SECRET_KEY" in result.output


def test_stencil_missing_key_reported(runner, tmp_env):
    result = runner.invoke(stencil_cmd, [str(tmp_env), "--key", "DOES_NOT_EXIST"])
    assert "Missing keys" in result.output or "Missing keys" in (result.output + result.output)
    # message goes to stderr which CliRunner mixes into output by default
    assert "DOES_NOT_EXIST" in result.output


def test_stencil_strict_exits_nonzero_on_missing(runner, tmp_env):
    result = runner.invoke(
        stencil_cmd, [str(tmp_env), "--key", "MISSING", "--strict"]
    )
    assert result.exit_code != 0


def test_stencil_strict_exits_zero_when_all_present(runner, tmp_env):
    result = runner.invoke(
        stencil_cmd, [str(tmp_env), "--key", "APP_NAME", "--strict"]
    )
    assert result.exit_code == 0


def test_stencil_writes_output_file(runner, tmp_env, tmp_path):
    out = tmp_path / "filtered.env"
    result = runner.invoke(
        stencil_cmd, [str(tmp_env), "--key", "APP_NAME", "--output", str(out)]
    )
    assert result.exit_code == 0
    assert out.exists()
    content = out.read_text()
    assert "APP_NAME" in content
    assert "DB_HOST" not in content


def test_dry_run_does_not_write(runner, tmp_env, tmp_path):
    out = tmp_path / "should_not_exist.env"
    runner.invoke(
        stencil_cmd,
        [str(tmp_env), "--key", "APP_NAME", "--output", str(out), "--dry-run"],
    )
    assert not out.exists()


def test_stencil_summary_in_output(runner, tmp_env):
    result = runner.invoke(stencil_cmd, [str(tmp_env), "--key", "APP_NAME", "--key", "DB_HOST"])
    assert "kept" in result.output
