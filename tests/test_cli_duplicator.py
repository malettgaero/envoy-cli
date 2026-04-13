"""Integration tests for the duplicates CLI command."""
import pytest
from click.testing import CliRunner
from pathlib import Path

from envoy.cli_duplicator import duplicates_cmd


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def tmp_env(tmp_path):
    def _make(content: str) -> str:
        p = tmp_path / ".env"
        p.write_text(content, encoding="utf-8")
        return str(p)
    return _make


def test_no_duplicates_reports_clean(runner, tmp_env):
    path = tmp_env("FOO=bar\nBAZ=qux\n")
    result = runner.invoke(duplicates_cmd, [path])
    assert result.exit_code == 0
    assert "No duplicate keys found" in result.output


def test_duplicate_detected_in_output(runner, tmp_env):
    path = tmp_env("FOO=first\nFOO=second\n")
    result = runner.invoke(duplicates_cmd, [path])
    assert result.exit_code == 0
    assert "FOO" in result.output
    assert "2 occurrences" in result.output


def test_strict_flag_exits_nonzero_on_duplicate(runner, tmp_env):
    path = tmp_env("KEY=a\nKEY=b\n")
    result = runner.invoke(duplicates_cmd, [path, "--strict"])
    assert result.exit_code == 1


def test_strict_flag_exits_zero_when_clean(runner, tmp_env):
    path = tmp_env("ONLY=once\n")
    result = runner.invoke(duplicates_cmd, [path, "--strict"])
    assert result.exit_code == 0


def test_multiple_duplicate_keys_listed(runner, tmp_env):
    path = tmp_env("A=1\nB=2\nA=3\nB=4\n")
    result = runner.invoke(duplicates_cmd, [path])
    assert "A" in result.output
    assert "B" in result.output
    assert "2 duplicate key(s)" in result.output


def test_comments_not_counted_as_duplicates(runner, tmp_env):
    path = tmp_env("# FOO=ignored\nFOO=real\n")
    result = runner.invoke(duplicates_cmd, [path])
    assert result.exit_code == 0
    assert "No duplicate keys found" in result.output
