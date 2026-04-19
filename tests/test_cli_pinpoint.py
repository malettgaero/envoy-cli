import pytest
from click.testing import CliRunner
from envoy.cli_pinpoint import pinpoint_cmd


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def tmp_envs(tmp_path):
    dev = tmp_path / ".env.dev"
    prod = tmp_path / ".env.prod"
    dev.write_text("DB_HOST=localhost\nDEBUG=true\nAPI_KEY=dev-key\n")
    prod.write_text("DB_HOST=prod.db\nAPI_KEY=prod-key\nLOG_LEVEL=warn\n")
    return str(dev), str(prod)


def test_key_found_in_both(runner, tmp_envs):
    dev, prod = tmp_envs
    r = runner.invoke(pinpoint_cmd, ["DB_HOST", "-f", dev, "-f", prod])
    assert "DB_HOST" in r.output
    assert "2 file(s)" in r.output


def test_inconsistent_flagged(runner, tmp_envs):
    dev, prod = tmp_envs
    r = runner.invoke(pinpoint_cmd, ["DB_HOST", "-f", dev, "-f", prod])
    assert "INCONSISTENT" in r.output
    assert r.exit_code == 2


def test_consistent_key_exits_zero(runner, tmp_envs):
    dev, prod = tmp_envs
    # LOG_LEVEL only in prod -> unique -> consistent
    r = runner.invoke(pinpoint_cmd, ["LOG_LEVEL", "-f", dev, "-f", prod])
    assert r.exit_code == 0
    assert "INCONSISTENT" not in r.output


def test_show_values_prints_value(runner, tmp_envs):
    dev, prod = tmp_envs
    r = runner.invoke(pinpoint_cmd, ["API_KEY", "-f", dev, "-f", prod, "--show-values"])
    assert "dev-key" in r.output
    assert "prod-key" in r.output


def test_missing_key_exits_nonzero(runner, tmp_envs):
    dev, prod = tmp_envs
    r = runner.invoke(pinpoint_cmd, ["NONEXISTENT", "-f", dev, "-f", prod])
    assert r.exit_code != 0
    assert "No matching keys" in r.output


def test_inconsistent_only_hides_consistent(runner, tmp_envs):
    dev, prod = tmp_envs
    r = runner.invoke(
        pinpoint_cmd,
        ["DB_HOST", "LOG_LEVEL", "-f", dev, "-f", prod, "--inconsistent-only"],
    )
    assert "DB_HOST" in r.output
    assert "LOG_LEVEL" not in r.output
