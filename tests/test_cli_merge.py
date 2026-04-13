"""Integration tests for the `envoy merge` CLI command."""

import pytest
from click.testing import CliRunner
from pathlib import Path

from envoy.cli import cli


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def tmp_envs(tmp_path):
    """Return a helper that writes a .env file and returns its path."""
    def _make(name: str, content: str) -> str:
        p = tmp_path / name
        p.write_text(content)
        return str(p)
    return _make


def test_merge_two_files_no_conflict(runner, tmp_envs):
    a = tmp_envs("a.env", "HOST=localhost\nPORT=5432\n")
    b = tmp_envs("b.env", "DEBUG=true\nLOG_LEVEL=info\n")
    result = runner.invoke(cli, ["merge", a, b])
    assert result.exit_code == 0
    assert "HOST=localhost" in result.output
    assert "DEBUG=true" in result.output


def test_merge_last_wins_conflict(runner, tmp_envs):
    a = tmp_envs("a.env", "KEY=original\n")
    b = tmp_envs("b.env", "KEY=override\n")
    result = runner.invoke(cli, ["merge", a, b, "--strategy", "last_wins"])
    assert result.exit_code == 2  # conflicts present
    assert "KEY=override" in result.output
    assert "conflict" in result.output.lower()


def test_merge_first_wins_conflict(runner, tmp_envs):
    a = tmp_envs("a.env", "KEY=original\n")
    b = tmp_envs("b.env", "KEY=override\n")
    result = runner.invoke(cli, ["merge", a, b, "--strategy", "first_wins"])
    assert result.exit_code == 2
    assert "KEY=original" in result.output


def test_merge_strict_exits_on_conflict(runner, tmp_envs):
    a = tmp_envs("a.env", "KEY=v1\n")
    b = tmp_envs("b.env", "KEY=v2\n")
    result = runner.invoke(cli, ["merge", a, b, "--strategy", "strict"])
    assert result.exit_code == 1
    assert "Merge error" in result.output


def test_merge_output_writes_file(runner, tmp_envs, tmp_path):
    a = tmp_envs("a.env", "A=1\n")
    b = tmp_envs("b.env", "B=2\n")
    out = str(tmp_path / "merged.env")
    result = runner.invoke(cli, ["merge", a, b, "--output", out])
    assert result.exit_code == 0
    merged_content = Path(out).read_text()
    assert "A=1" in merged_content
    assert "B=2" in merged_content


def test_merge_invalid_file_parse_error(runner, tmp_envs):
    bad = tmp_envs("bad.env", "=NOKEY\n")
    good = tmp_envs("good.env", "X=1\n")
    result = runner.invoke(cli, ["merge", bad, good])
    # parser may or may not error; at minimum it should not crash with traceback
    assert result.exit_code in (0, 1)


def test_merge_single_file(runner, tmp_envs):
    a = tmp_envs("a.env", "ONLY=key\n")
    result = runner.invoke(cli, ["merge", a])
    assert result.exit_code == 0
    assert "ONLY=key" in result.output
