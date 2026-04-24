"""CLI integration tests for the inject command."""
import os
from click.testing import CliRunner
import pytest
from envoy.cli_inject import inject_cmd
from envoy.parser import parse_env_file


@pytest.fixture
def runner():
    return CliRunner()


def _make(tmp_path, name, content):
    p = tmp_path / name
    p.write_text(content)
    return str(p)


@pytest.fixture
def tmp_envs(tmp_path):
    base = _make(tmp_path, ".env.base", "APP_HOST=localhost\nAPP_PORT=8080\n")
    source = _make(tmp_path, ".env.source", "APP_PORT=9090\nSECRET_KEY=abc123\n")
    return base, source, tmp_path


def test_inject_new_key(runner, tmp_envs):
    base, source, _ = tmp_envs
    result = runner.invoke(inject_cmd, [base, source])
    assert result.exit_code == 0
    env = parse_env_file(base)
    assert env["SECRET_KEY"] == "abc123"


def test_inject_overwrites_existing_key(runner, tmp_envs):
    base, source, _ = tmp_envs
    runner.invoke(inject_cmd, [base, source])
    env = parse_env_file(base)
    assert env["APP_PORT"] == "9090"


def test_inject_no_overwrite_preserves_base(runner, tmp_envs):
    base, source, _ = tmp_envs
    runner.invoke(inject_cmd, [base, source, "--no-overwrite"])
    env = parse_env_file(base)
    assert env["APP_PORT"] == "8080"


def test_inject_dry_run_does_not_write(runner, tmp_envs):
    base, source, _ = tmp_envs
    runner.invoke(inject_cmd, [base, source, "--dry-run"])
    env = parse_env_file(base)
    assert "SECRET_KEY" not in env


def test_inject_specific_key_only(runner, tmp_envs):
    base, source, _ = tmp_envs
    runner.invoke(inject_cmd, [base, source, "--key", "SECRET_KEY"])
    env = parse_env_file(base)
    assert env["SECRET_KEY"] == "abc123"
    assert env["APP_PORT"] == "8080"  # not touched


def test_inject_output_file(runner, tmp_envs, tmp_path):
    base, source, _ = tmp_envs
    out = str(tmp_path / ".env.out")
    runner.invoke(inject_cmd, [base, source, "--output", out])
    assert os.path.exists(out)
    env = parse_env_file(out)
    assert "SECRET_KEY" in env


def test_inject_output_shows_summary(runner, tmp_envs):
    base, source, _ = tmp_envs
    result = runner.invoke(inject_cmd, [base, source, "--dry-run"])
    assert "injected" in result.output
