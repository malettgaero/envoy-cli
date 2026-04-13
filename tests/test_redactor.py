"""Tests for envoy.redactor."""
import pytest
from envoy.redactor import redact_env, _DEFAULT_MASK


def _env(**kwargs) -> dict:
    return dict(kwargs)


def test_non_sensitive_keys_unchanged():
    env = _env(APP_NAME="myapp", PORT="8080")
    result = redact_env(env)
    assert result.env["APP_NAME"] == "myapp"
    assert result.env["PORT"] == "8080"
    assert result.redacted_keys == []


def test_auto_detect_password():
    env = _env(DB_PASSWORD="s3cr3t", HOST="localhost")
    result = redact_env(env)
    assert result.env["DB_PASSWORD"] == _DEFAULT_MASK
    assert result.env["HOST"] == "localhost"
    assert "DB_PASSWORD" in result.redacted_keys


def test_auto_detect_token():
    env = _env(GITHUB_TOKEN="abc123")
    result = redact_env(env)
    assert result.env["GITHUB_TOKEN"] == _DEFAULT_MASK


def test_auto_detect_api_key():
    env = _env(STRIPE_API_KEY="sk_live_xxx")
    result = redact_env(env)
    assert result.env["STRIPE_API_KEY"] == _DEFAULT_MASK


def test_explicit_key_redacted():
    env = _env(MY_CUSTOM="value", OTHER="ok")
    result = redact_env(env, keys=["MY_CUSTOM"])
    assert result.env["MY_CUSTOM"] == _DEFAULT_MASK
    assert result.env["OTHER"] == "ok"


def test_custom_mask_string():
    env = _env(DB_SECRET="topsecret")
    result = redact_env(env, mask="[HIDDEN]")
    assert result.env["DB_SECRET"] == "[HIDDEN]"


def test_strip_removes_key_value():
    env = _env(API_KEY="xyz", SAFE="yes")
    result = redact_env(env, strip=True)
    assert result.env["API_KEY"] == ""
    assert "API_KEY" in result.redacted_keys


def test_auto_detect_disabled():
    env = _env(DB_PASSWORD="secret")
    result = redact_env(env, auto_detect=False)
    assert result.env["DB_PASSWORD"] == "secret"
    assert result.redacted_keys == []


def test_extra_patterns_used():
    env = _env(INTERNAL_CERT="pem_data", OTHER="fine")
    result = redact_env(env, extra_patterns=["CERT"])
    assert result.env["INTERNAL_CERT"] == _DEFAULT_MASK
    assert result.env["OTHER"] == "fine"


def test_summary_no_redactions():
    env = _env(HOST="localhost")
    result = redact_env(env)
    assert result.summary() == "No keys redacted."


def test_summary_with_redactions():
    env = _env(DB_PASSWORD="x", APP_SECRET="y")
    result = redact_env(env)
    assert "2 key(s) redacted" in result.summary()


def test_to_dict_fields():
    env = _env(TOKEN="abc")
    result = redact_env(env)
    entry_dict = result.entries[0].to_dict()
    assert entry_dict["key"] == "TOKEN"
    assert entry_dict["redacted"] is True
    assert entry_dict["value"] == _DEFAULT_MASK


def test_empty_env_returns_empty_result():
    result = redact_env({})
    assert result.env == {}
    assert result.redacted_keys == []
