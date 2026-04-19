import pytest
from click.testing import CliRunner
from pathlib import Path
from envoy.cli_expiry import expiry_cmd


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


def test_no_date_keys_reports_none(runner, tmp_env):
    f = tmp_env("API_KEY=abc123\nDEBUG=true\n")
    result = runner.invoke(expiry_cmd, [f])
    assert result.exit_code == 0
    assert "No date keys found" in result.output


def test_expired_key_shown(runner, tmp_env):
    f = tmp_env("CERT_EXPIRY=2020-01-01\n")
    result = runner.invoke(expiry_cmd, [f])
    assert result.exit_code == 0
    assert "CERT_EXPIRY" in result.output
    assert "EXPIRED" in result.output


def test_future_key_shown_as_ok(runner, tmp_env):
    f = tmp_env("RENEWAL=2099-12-31\n")
    result = runner.invoke(expiry_cmd, [f])
    assert "OK" in result.output


def test_strict_exits_nonzero_on_expired(runner, tmp_env):
    f = tmp_env("CERT_EXPIRY=2020-01-01\n")
    result = runner.invoke(expiry_cmd, [f, "--strict"])
    assert result.exit_code == 1


def test_strict_exits_zero_when_no_expired(runner, tmp_env):
    f = tmp_env("RENEWAL=2099-12-31\n")
    result = runner.invoke(expiry_cmd, [f, "--strict"])
    assert result.exit_code == 0


def test_filter_by_key(runner, tmp_env):
    f = tmp_env("CERT_EXPIRY=2020-01-01\nRENEWAL=2099-12-31\n")
    result = runner.invoke(expiry_cmd, [f, "--key", "RENEWAL"])
    assert "RENEWAL" in result.output
    assert "CERT_EXPIRY" not in result.output


def test_summary_line_present(runner, tmp_env):
    f = tmp_env("CERT_EXPIRY=2020-06-01\n")
    result = runner.invoke(expiry_cmd, [f])
    assert "checked" in result.output
