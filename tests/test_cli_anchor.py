"""CLI tests for the anchor command."""
import pytest
from click.testing import CliRunner
from envoy.cli_anchor import anchor_cmd
from envoy.parser import parse_env_file


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def tmp_env(tmp_path):
    p = tmp_path / ".env"
    p.write_text("APP_NAME=myapp\nDB_HOST=localhost\nSECRET_KEY=abc\nLOG_LEVEL=info\n")
    return str(p)


def test_anchor_top_rewrites_file(runner, tmp_env):
    result = runner.invoke(anchor_cmd, [tmp_env, "--top", "SECRET_KEY"])
    assert result.exit_code == 0
    env = parse_env_file(tmp_env)
    keys = list(env.keys())
    assert keys[0] == "SECRET_KEY"


def test_anchor_bottom_rewrites_file(runner, tmp_env):
    result = runner.invoke(anchor_cmd, [tmp_env, "--bottom", "LOG_LEVEL"])
    assert result.exit_code == 0
    env = parse_env_file(tmp_env)
    keys = list(env.keys())
    assert keys[-1] == "LOG_LEVEL"


def test_dry_run_does_not_write(runner, tmp_env):
    original = open(tmp_env).read()
    result = runner.invoke(anchor_cmd, [tmp_env, "--top", "LOG_LEVEL", "--dry-run"])
    assert result.exit_code == 0
    assert open(tmp_env).read() == original


def test_no_change_reports_no_reorder(runner, tmp_env):
    result = runner.invoke(anchor_cmd, [tmp_env])
    assert result.exit_code == 0
    assert "No reordering needed" in result.output


def test_summary_shown_in_output(runner, tmp_env):
    result = runner.invoke(anchor_cmd, [tmp_env, "--top", "APP_NAME", "--bottom", "LOG_LEVEL"])
    assert result.exit_code == 0
    assert "Anchor summary" in result.output


def test_quiet_suppresses_output(runner, tmp_env):
    result = runner.invoke(anchor_cmd, [tmp_env, "--top", "SECRET_KEY", "--quiet"])
    assert result.exit_code == 0
    assert result.output.strip() == ""


def test_invalid_group_spec_exits_nonzero(runner, tmp_env):
    result = runner.invoke(anchor_cmd, [tmp_env, "--group", "badspec"])
    assert result.exit_code != 0


def test_group_tag_shown_in_output(runner, tmp_env):
    result = runner.invoke(anchor_cmd, [tmp_env, "--group", "db:DB_HOST"])
    assert result.exit_code == 0
    assert "[group]" in result.output
