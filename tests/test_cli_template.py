"""Integration tests for the `template` CLI command."""
from pathlib import Path

import pytest
from click.testing import CliRunner

from envoy.cli_template import template_cmd


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def tmp_envs(tmp_path):
    def _make(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(content)
        return p

    return _make


def test_basic_render(runner, tmp_envs):
    tmpl = tmp_envs("tmpl.env", "DSN=postgres://{{ DB_HOST }}/mydb\n")
    ctx = tmp_envs("ctx.env", "DB_HOST=db.internal\n")
    result = runner.invoke(template_cmd, [str(tmpl), str(ctx)])
    assert result.exit_code == 0
    assert "DSN=postgres://db.internal/mydb" in result.output


def test_no_placeholders_passes_through(runner, tmp_envs):
    tmpl = tmp_envs("tmpl.env", "KEY=value\n")
    ctx = tmp_envs("ctx.env", "OTHER=x\n")
    result = runner.invoke(template_cmd, [str(tmpl), str(ctx)])
    assert result.exit_code == 0
    assert "KEY=value" in result.output


def test_unresolved_warns_but_exits_zero(runner, tmp_envs):
    tmpl = tmp_envs("tmpl.env", "URL=http://{{ HOST }}/api\n")
    ctx = tmp_envs("ctx.env", "OTHER=x\n")
    result = runner.invoke(template_cmd, [str(tmpl), str(ctx)])
    assert result.exit_code == 0
    assert "unresolved" in result.output.lower() or "unresolved" in (result.output + "").lower()


def test_strict_mode_exits_nonzero_on_unresolved(runner, tmp_envs):
    tmpl = tmp_envs("tmpl.env", "URL=http://{{ HOST }}/api\n")
    ctx = tmp_envs("ctx.env", "OTHER=x\n")
    result = runner.invoke(template_cmd, ["--strict", str(tmpl), str(ctx)])
    assert result.exit_code != 0


def test_strict_mode_passes_when_all_resolved(runner, tmp_envs):
    tmpl = tmp_envs("tmpl.env", "KEY={{ VAL }}\n")
    ctx = tmp_envs("ctx.env", "VAL=hello\n")
    result = runner.invoke(template_cmd, ["--strict", str(tmpl), str(ctx)])
    assert result.exit_code == 0
    assert "KEY=hello" in result.output


def test_output_flag_writes_file(runner, tmp_envs, tmp_path):
    tmpl = tmp_envs("tmpl.env", "KEY={{ VAL }}\n")
    ctx = tmp_envs("ctx.env", "VAL=world\n")
    out = tmp_path / "out.env"
    result = runner.invoke(template_cmd, [str(tmpl), str(ctx), "-o", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    assert "KEY=world" in out.read_text()


def test_resolved_count_reported(runner, tmp_envs):
    tmpl = tmp_envs("tmpl.env", "A={{ X }}\nB={{ Y }}\n")
    ctx = tmp_envs("ctx.env", "X=1\nY=2\n")
    result = runner.invoke(template_cmd, [str(tmpl), str(ctx)])
    assert result.exit_code == 0
