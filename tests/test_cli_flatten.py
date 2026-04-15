"""CLI tests for the flatten command."""
import pytest
from click.testing import CliRunner
from envoy.cli_flatten import flatten_cmd


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def tmp_env(tmp_path):
    p = tmp_path / ".env"
    p.write_text("DB.HOST=localhost\nDB.PORT=5432\nAPP_NAME=myapp\n")
    return str(p)


def test_apply_writes_flat_keys(runner, tmp_env):
    result = runner.invoke(flatten_cmd, ["apply", tmp_env])
    assert result.exit_code == 0
    content = open(tmp_env).read()
    assert "DB__HOST" in content
    assert "DB__PORT" in content
    assert "APP_NAME" in content


def test_apply_dry_run_does_not_write(runner, tmp_env):
    original = open(tmp_env).read()
    result = runner.invoke(flatten_cmd, ["apply", tmp_env, "--dry-run"])
    assert result.exit_code == 0
    assert open(tmp_env).read() == original


def test_apply_shows_mapping_in_output(runner, tmp_env):
    result = runner.invoke(flatten_cmd, ["apply", tmp_env])
    assert "DB.HOST" in result.output
    assert "DB__HOST" in result.output


def test_apply_quiet_suppresses_output(runner, tmp_env):
    result = runner.invoke(flatten_cmd, ["apply", tmp_env, "--quiet"])
    assert result.exit_code == 0
    assert result.output.strip() == ""


def test_apply_custom_separator(runner, tmp_path):
    p = tmp_path / ".env"
    p.write_text("DB.HOST=localhost\n")
    result = runner.invoke(flatten_cmd, ["apply", str(p), "--separator", "-"])
    assert result.exit_code == 0
    assert "DB-HOST" in open(str(p)).read()


def test_undo_restores_dot_notation(runner, tmp_path):
    p = tmp_path / ".env"
    p.write_text("DB__HOST=localhost\nDB__PORT=5432\n")
    result = runner.invoke(flatten_cmd, ["undo", str(p)])
    assert result.exit_code == 0
    content = open(str(p)).read()
    assert "DB.HOST" in content
    assert "DB.PORT" in content


def test_undo_dry_run_does_not_write(runner, tmp_path):
    p = tmp_path / ".env"
    p.write_text("DB__HOST=localhost\n")
    original = p.read_text()
    result = runner.invoke(flatten_cmd, ["undo", str(p), "--dry-run"])
    assert result.exit_code == 0
    assert p.read_text() == original
