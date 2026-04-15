"""Integration tests for the `envoy extract` CLI command."""
from pathlib import Path

import pytest
from click.testing import CliRunner

from envoy.cli_extract import extract_cmd
from envoy.parser import parse_env_file


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def tmp_env(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        "APP_NAME=myapp\nAPP_ENV=production\nDB_HOST=localhost\nDB_PORT=5432\nSECRET=s3cr3t\n"
    )
    return p


def test_extract_exact_key_output(runner, tmp_env):
    result = runner.invoke(extract_cmd, [str(tmp_env), "-k", "APP_NAME"])
    assert result.exit_code == 0
    assert "APP_NAME" in result.output


def test_extract_pattern_output(runner, tmp_env):
    result = runner.invoke(extract_cmd, [str(tmp_env), "-p", "DB_*"])
    assert result.exit_code == 0
    assert "DB_HOST" in result.output
    assert "DB_PORT" in result.output


def test_extract_writes_output_file(runner, tmp_env, tmp_path):
    out = tmp_path / "extracted.env"
    result = runner.invoke(
        extract_cmd, [str(tmp_env), "-k", "APP_NAME", "-o", str(out)]
    )
    assert result.exit_code == 0
    assert out.exists()
    env = parse_env_file(out)
    assert env == {"APP_NAME": "myapp"}


def test_extract_dry_run_does_not_write(runner, tmp_env, tmp_path):
    out = tmp_path / "extracted.env"
    result = runner.invoke(
        extract_cmd, [str(tmp_env), "-k", "APP_NAME", "-o", str(out), "--dry-run"]
    )
    assert result.exit_code == 0
    assert not out.exists()
    assert "dry-run" in result.output


def test_extract_no_match_exits_nonzero(runner, tmp_env):
    result = runner.invoke(extract_cmd, [str(tmp_env), "-k", "NONEXISTENT"])
    assert result.exit_code != 0


def test_extract_show_excluded_lists_skipped_keys(runner, tmp_env):
    result = runner.invoke(
        extract_cmd, [str(tmp_env), "-k", "APP_NAME", "--show-excluded"]
    )
    assert result.exit_code == 0
    assert "DB_HOST" in result.output


def test_extract_no_keys_no_patterns_extracts_all(runner, tmp_env, tmp_path):
    out = tmp_path / "all.env"
    result = runner.invoke(extract_cmd, [str(tmp_env), "-o", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    env = parse_env_file(out)
    assert len(env) == 5
