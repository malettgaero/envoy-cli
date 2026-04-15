"""CLI integration tests for the promote command."""
import os
import pytest
from click.testing import CliRunner
from envoy.cli_promote import promote_cmd


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


def test_promote_new_key(runner, tmp_envs):
    src = tmp_envs("src.env", "FEATURE_FLAG=true\n")
    tgt = tmp_envs("tgt.env", "DB_HOST=localhost\n")
    result = runner.invoke(promote_cmd, ["apply", src, tgt])
    assert result.exit_code == 0
    assert "[new]" in result.output
    assert "FEATURE_FLAG" in result.output


def test_promote_overwrites_existing_key(runner, tmp_envs):
    src = tmp_envs("src.env", "DB_HOST=prod-db\n")
    tgt = tmp_envs("tgt.env", "DB_HOST=localhost\n")
    result = runner.invoke(promote_cmd, ["apply", src, tgt])
    assert result.exit_code == 0
    assert "[overwrite]" in result.output


def test_promote_no_overwrite_skips_existing(runner, tmp_envs):
    src = tmp_envs("src.env", "DB_HOST=prod-db\n")
    tgt = tmp_envs("tgt.env", "DB_HOST=localhost\n")
    result = runner.invoke(promote_cmd, ["apply", "--no-overwrite", src, tgt])
    assert result.exit_code == 0
    assert "Nothing to promote" in result.output or "Skipped" in result.output


def test_promote_dry_run_does_not_write(runner, tmp_envs):
    src = tmp_envs("src.env", "NEW_KEY=value\n")
    tgt = tmp_envs("tgt.env", "EXISTING=1\n")
    original = open(tgt.replace("tgt.env", "tgt.env")).read() if False else ""
    tgt_path = tgt
    before = open(tgt_path).read()
    result = runner.invoke(promote_cmd, ["apply", "--dry-run", src, tgt_path])
    after = open(tgt_path).read()
    assert result.exit_code == 0
    assert "Dry-run" in result.output
    assert before == after


def test_promote_specific_keys_only(runner, tmp_envs):
    src = tmp_envs("src.env", "A=1\nB=2\nC=3\n")
    tgt = tmp_envs("tgt.env", "")
    result = runner.invoke(promote_cmd, ["apply", "-k", "A", "-k", "C", src, tgt])
    assert result.exit_code == 0
    content = open(tgt).read()
    assert "A" in content
    assert "C" in content
    assert "B" not in content


def test_promote_missing_key_reported_as_skipped(runner, tmp_envs):
    src = tmp_envs("src.env", "A=1\n")
    tgt = tmp_envs("tgt.env", "")
    result = runner.invoke(promote_cmd, ["apply", "-k", "GHOST", src, tgt])
    assert result.exit_code == 0
    assert "Nothing to promote" in result.output or "Skipped" in result.output
