import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envoy.cli_freeze import freeze_cmd


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def tmp_env(tmp_path):
    p = tmp_path / ".env"
    p.write_text("APP=envoy\nDEBUG=false\nPORT=8080\n")
    return p


def test_lock_creates_lock_file(runner, tmp_env):
    lock = tmp_env.with_suffix(".env.lock")
    result = runner.invoke(freeze_cmd, ["lock", str(tmp_env)])
    assert result.exit_code == 0
    assert lock.exists()
    data = json.loads(lock.read_text())
    assert "checksum" in data


def test_lock_output_contains_checksum(runner, tmp_env):
    result = runner.invoke(freeze_cmd, ["lock", str(tmp_env)])
    assert "Checksum:" in result.output


def test_verify_passes_after_lock(runner, tmp_env):
    runner.invoke(freeze_cmd, ["lock", str(tmp_env)])
    result = runner.invoke(freeze_cmd, ["verify", str(tmp_env)])
    assert result.exit_code == 0
    assert "OK" in result.output


def test_verify_fails_after_tampering(runner, tmp_env):
    runner.invoke(freeze_cmd, ["lock", str(tmp_env)])
    tmp_env.write_text("APP=envoy\nDEBUG=false\nPORT=8080\nINJECTED=evil\n")
    result = runner.invoke(freeze_cmd, ["verify", str(tmp_env)])
    assert "TAMPERED" in result.output


def test_verify_strict_exits_nonzero_on_tamper(runner, tmp_env):
    runner.invoke(freeze_cmd, ["lock", str(tmp_env)])
    tmp_env.write_text("APP=changed\n")
    result = runner.invoke(freeze_cmd, ["verify", "--strict", str(tmp_env)])
    assert result.exit_code != 0


def test_verify_missing_lock_exits_with_error(runner, tmp_env):
    result = runner.invoke(freeze_cmd, ["verify", str(tmp_env)])
    assert result.exit_code != 0


def test_lock_custom_lock_file(runner, tmp_env, tmp_path):
    custom = tmp_path / "custom.lock"
    result = runner.invoke(freeze_cmd, ["lock", str(tmp_env), "--lock-file", str(custom)])
    assert result.exit_code == 0
    assert custom.exists()
