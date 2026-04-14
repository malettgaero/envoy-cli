"""CLI tests for the `group` command."""
import pytest
from click.testing import CliRunner
from envoy.cli_grouper import group_cmd


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def tmp_env(tmp_path):
    p = tmp_path / ".env"
    p.write_text(
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "AWS_KEY=AKIA\n"
        "DEBUG=true\n"
    )
    return str(p)


def test_group_shows_prefixes(runner, tmp_env):
    result = runner.invoke(group_cmd, [tmp_env])
    assert result.exit_code == 0
    assert "[DB]" in result.output
    assert "[AWS]" in result.output


def test_group_shows_ungrouped(runner, tmp_env):
    result = runner.invoke(group_cmd, [tmp_env])
    assert result.exit_code == 0
    assert "(ungrouped)" in result.output
    assert "DEBUG" in result.output


def test_group_explicit_prefix(runner, tmp_env):
    result = runner.invoke(group_cmd, [tmp_env, "--prefix", "DB"])
    assert result.exit_code == 0
    assert "[DB]" in result.output
    assert "DB_HOST" in result.output


def test_group_show_values(runner, tmp_env):
    result = runner.invoke(group_cmd, [tmp_env, "--show-values"])
    assert result.exit_code == 0
    assert "localhost" in result.output


def test_group_no_auto_all_ungrouped(runner, tmp_env):
    result = runner.invoke(group_cmd, [tmp_env, "--no-auto"])
    assert result.exit_code == 0
    assert "(ungrouped)" in result.output
    # No prefix-labelled sections
    assert "[DB]" not in result.output


def test_group_summary_in_output(runner, tmp_env):
    result = runner.invoke(group_cmd, [tmp_env])
    assert result.exit_code == 0
    # summary line contains key counts
    assert "key(s)" in result.output


def test_group_empty_file(runner, tmp_path):
    p = tmp_path / ".env"
    p.write_text("")
    result = runner.invoke(group_cmd, [str(p)])
    assert result.exit_code == 0
    assert "No keys found" in result.output
