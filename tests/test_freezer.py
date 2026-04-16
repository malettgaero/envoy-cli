import pytest
from envoy.freezer import freeze_env, verify_env, save_freeze, load_checksum, FreezeResult
from pathlib import Path
import json


@pytest.fixture
def base_env():
    return {"APP_NAME": "envoy", "DEBUG": "false", "PORT": "8080"}


def test_freeze_returns_freeze_result(base_env):
    result = freeze_env(base_env)
    assert isinstance(result, FreezeResult)


def test_freeze_checksum_is_hex_string(base_env):
    result = freeze_env(base_env)
    assert len(result.checksum) == 64
    int(result.checksum, 16)  # must be valid hex


def test_freeze_same_env_produces_same_checksum(base_env):
    r1 = freeze_env(base_env)
    r2 = freeze_env(dict(base_env))
    assert r1.checksum == r2.checksum


def test_freeze_different_env_produces_different_checksum(base_env):
    r1 = freeze_env(base_env)
    modified = dict(base_env)
    modified["PORT"] = "9090"
    r2 = freeze_env(modified)
    assert r1.checksum != r2.checksum


def test_verify_unchanged_env_passes(base_env):
    frozen = freeze_env(base_env)
    result = verify_env(base_env, frozen.checksum)
    assert result.passed


def test_verify_tampered_env_fails(base_env):
    frozen = freeze_env(base_env)
    tampered = dict(base_env)
    tampered["SECRET"] = "injected"
    result = verify_env(tampered, frozen.checksum)
    assert not result.passed
    assert len(result.violations) == 1
    assert "mismatch" in result.violations[0].reason


def test_verify_summary_ok(base_env):
    frozen = freeze_env(base_env)
    result = verify_env(base_env, frozen.checksum)
    assert result.summary().startswith("OK")


def test_verify_summary_tampered(base_env):
    frozen = freeze_env(base_env)
    result = verify_env({}, frozen.checksum)
    assert "TAMPERED" in result.summary()


def test_save_and_load_checksum(tmp_path, base_env):
    p = tmp_path / ".env.lock"
    frozen = freeze_env(base_env)
    save_freeze(frozen, p)
    loaded = load_checksum(p)
    assert loaded == frozen.checksum


def test_load_checksum_missing_file(tmp_path):
    result = load_checksum(tmp_path / "nonexistent.lock")
    assert result is None
