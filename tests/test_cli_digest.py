"""CLI tests for the digest command."""
import hashlib
import pytest
from click.testing import CliRunner
from envoy.cli_digest import digest_cmd


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def tmp_env(tmp_path):
    p = tmp_path / ".env"
    p.write_text("API_KEY=secret\nHOST=localhost\nPORT=8080\n")
    return str(p)


def test_digest_exits_zero(runner, tmp_env):
    result = runner.invoke(digest_cmd, [tmp_env])
    assert result.exit_code == 0


def test_digest_shows_key_names(runner, tmp_env):
    result = runner.invoke(digest_cmd, [tmp_env])
    assert "API_KEY" in result.output
    assert "HOST" in result.output


def test_digest_shows_algorithm(runner, tmp_env):
    result = runner.invoke(digest_cmd, [tmp_env])
    assert "sha256" in result.output


def test_digest_md5_algo(runner, tmp_env):
    result = runner.invoke(digest_cmd, [tmp_env, "--algo", "md5"])
    assert result.exit_code == 0
    assert "md5" in result.output


def test_digest_short_flag_truncates(runner, tmp_env):
    result = runner.invoke(digest_cmd, [tmp_env, "--short"])
    full = hashlib.sha256(b"secret").hexdigest()
    assert full not in result.output
    assert full[:12] in result.output


def test_digest_key_filter(runner, tmp_env):
    result = runner.invoke(digest_cmd, [tmp_env, "--key", "HOST"])
    assert "HOST" in result.output
    assert "API_KEY" not in result.output


def test_digest_unsupported_algo_shows_error(runner, tmp_env):
    result = runner.invoke(digest_cmd, [tmp_env, "--algo", "crc32"])
    assert result.exit_code != 0
    assert "Unsupported" in result.output


def test_digest_summary_line(runner, tmp_env):
    result = runner.invoke(digest_cmd, [tmp_env])
    assert "digested" in result.output


def test_digest_empty_file_reports_no_keys(runner, tmp_path):
    p = tmp_path / ".env"
    p.write_text("")
    result = runner.invoke(digest_cmd, [str(p)])
    assert result.exit_code == 0
    assert "No keys" in result.output
