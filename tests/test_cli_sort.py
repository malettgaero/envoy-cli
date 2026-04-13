"""Integration tests for the sort CLI command."""
import pytest
from click.testing import CliRunner
from envoy.cli_sort import sort_cmd
import os


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def tmp_env(tmp_path):
    def _make(content: str) -> str:
        p = tmp_path / ".env"
        p.write_text(content)
        return str(p)
    return _make


def test_sort_writes_sorted_file(runner, tmp_env):
    path = tmp_env("ZEBRA=1\nAPPLE=2\nMANGO=3\n")
    result = runner.invoke(sort_cmd, [path])
    assert result.exit_code == 0
    content = open(path).read()
    keys = [line.split("=")[0] for line in content.splitlines() if "=" in line]
    assert keys == sorted(keys, key=lambda k: k.lower())


def test_sort_already_sorted_reports_no_change(runner, tmp_env):
    path = tmp_env("ALPHA=1\nBETA=2\nGAMMA=3\n")
    result = runner.invoke(sort_cmd, [path])
    assert result.exit_code == 0
    assert "already" in result.output


def test_dry_run_does_not_write(runner, tmp_env):
    original = "ZEBRA=1\nAPPLE=2\n"
    path = tmp_env(original)
    result = runner.invoke(sort_cmd, [path, "--dry-run"])
    assert result.exit_code == 0
    assert open(path).read() == original
    assert "APPLE" in result.output


def test_dry_run_shows_sorted_preview(runner, tmp_env):
    path = tmp_env("Z=1\nA=2\nM=3\n")
    result = runner.invoke(sort_cmd, [path, "--dry-run"])
    lines = [l for l in result.output.splitlines() if "=" in l]
    keys = [l.split("=")[0] for l in lines]
    assert keys == sorted(keys, key=lambda k: k.lower())


def test_group_option_pins_key_to_top(runner, tmp_env):
    path = tmp_env("Z=1\nA=2\nPRIORITY=0\n")
    result = runner.invoke(sort_cmd, [path, "--group", "PRIORITY"])
    assert result.exit_code == 0
    content = open(path).read()
    keys = [line.split("=")[0] for line in content.splitlines() if "=" in line]
    assert keys[0] == "PRIORITY"


def test_case_sensitive_flag(runner, tmp_env):
    path = tmp_env("b=1\nA=2\nc=3\n")
    result = runner.invoke(sort_cmd, [path, "--case-sensitive"])
    assert result.exit_code == 0
    content = open(path).read()
    keys = [line.split("=")[0] for line in content.splitlines() if "=" in line]
    assert keys == sorted(keys)
