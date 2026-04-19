import pytest
from click.testing import CliRunner
from pathlib import Path
from envoy.cli_trace import trace_cmd


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def tmp_envs(tmp_path):
    def _make(name, content):
        p = tmp_path / name
        p.write_text(content)
        return str(p)
    return _make


def test_trace_shows_active_keys(runner, tmp_envs):
    base = tmp_envs(".env.base", "APP=myapp\nDEBUG=false\n")
    local = tmp_envs(".env.local", "DEBUG=true\n")
    result = runner.invoke(trace_cmd, [base, local])
    assert result.exit_code == 0
    assert "APP=myapp" in result.output
    assert "DEBUG=true" in result.output


def test_trace_shows_source_label(runner, tmp_envs):
    base = tmp_envs(".env", "PORT=8000\n")
    result = runner.invoke(trace_cmd, [base])
    assert result.exit_code == 0
    assert ".env" in result.output


def test_trace_key_filter(runner, tmp_envs):
    base = tmp_envs(".env.base", "APP=myapp\nDEBUG=false\n")
    local = tmp_envs(".env.local", "DEBUG=true\n")
    result = runner.invoke(trace_cmd, ["--key", "DEBUG", base, local])
    assert result.exit_code == 0
    assert "DEBUG" in result.output
    assert "APP" not in result.output


def test_trace_key_missing_exits_nonzero(runner, tmp_envs):
    base = tmp_envs(".env", "A=1\n")
    result = runner.invoke(trace_cmd, ["--key", "MISSING", base])
    assert result.exit_code != 0


def test_trace_show_overridden_flag(runner, tmp_envs):
    base = tmp_envs(".env.base", "PORT=8000\n")
    override = tmp_envs(".env.override", "PORT=9000\n")
    result = runner.invoke(trace_cmd, ["--show-overridden", base, override])
    assert result.exit_code == 0
    assert "Shadowed" in result.output
    assert "PORT=8000" in result.output


def test_trace_no_overrides_no_shadowed_section(runner, tmp_envs):
    base = tmp_envs(".env", "A=1\nB=2\n")
    result = runner.invoke(trace_cmd, ["--show-overridden", base])
    assert result.exit_code == 0
    assert "Shadowed" not in result.output
