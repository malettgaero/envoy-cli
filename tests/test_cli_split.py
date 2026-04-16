"""CLI tests for the split command."""
import pytest
from click.testing import CliRunner
from pathlib import Path

from envoy.cli_split import split_cmd


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def tmp_env(tmp_path):
    p = tmp_path / ".env"
    p.write_text(
        "DB_HOST=localhost\nDB_PORT=5432\nREDIS_URL=redis://localhost\nAPP_NAME=myapp\n"
    )
    return p


def test_split_creates_output_files(runner, tmp_env, tmp_path):
    db_out = tmp_path / "db.env"
    redis_out = tmp_path / "redis.env"
    result = runner.invoke(
        split_cmd,
        [
            str(tmp_env),
            "--prefix", f"^DB_:{db_out}",
            "--prefix", f"^REDIS_:{redis_out}",
        ],
    )
    assert result.exit_code == 0
    assert db_out.exists()
    assert redis_out.exists()


def test_split_output_contains_correct_keys(runner, tmp_env, tmp_path):
    db_out = tmp_path / "db.env"
    runner.invoke(split_cmd, [str(tmp_env), "--prefix", f"^DB_:{db_out}"])
    content = db_out.read_text()
    assert "DB_HOST" in content
    assert "DB_PORT" in content
    assert "REDIS_URL" not in content


def test_dry_run_does_not_write(runner, tmp_env, tmp_path):
    db_out = tmp_path / "db.env"
    runner.invoke(
        split_cmd,
        [str(tmp_env), "--prefix", f"^DB_:{db_out}", "--dry-run"],
    )
    assert not db_out.exists()


def test_unmatched_keys_reported(runner, tmp_env, tmp_path):
    db_out = tmp_path / "db.env"
    result = runner.invoke(
        split_cmd,
        [str(tmp_env), "--prefix", f"^DB_:{db_out}", "--dry-run"],
    )
    assert "unmatched" in result.output


def test_default_file_captures_unmatched(runner, tmp_env, tmp_path):
    db_out = tmp_path / "db.env"
    other_out = tmp_path / "other.env"
    result = runner.invoke(
        split_cmd,
        [
            str(tmp_env),
            "--prefix", f"^DB_:{db_out}",
            "--default", str(other_out),
        ],
    )
    assert result.exit_code == 0
    assert other_out.exists()
    content = other_out.read_text()
    assert "APP_NAME" in content


def test_invalid_prefix_format_exits_nonzero(runner, tmp_env):
    result = runner.invoke(split_cmd, [str(tmp_env), "--prefix", "BADFORMAT"])
    assert result.exit_code != 0
