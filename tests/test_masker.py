"""Tests for envoy.masker."""
import pytest
from envoy.masker import mask_env, DEFAULT_MASK


@pytest.fixture()
def base_env():
    return {
        "APP_NAME": "myapp",
        "DB_PASSWORD": "s3cr3t",
        "API_KEY": "abc123",
        "PORT": "8080",
        "AUTH_TOKEN": "tok-xyz",
        "DEBUG": "true",
    }


def test_non_sensitive_keys_unchanged(base_env):
    result = mask_env(base_env)
    assert result.env["APP_NAME"] == "myapp"
    assert result.env["PORT"] == "8080"
    assert result.env["DEBUG"] == "true"


def test_sensitive_keys_masked(base_env):
    result = mask_env(base_env)
    assert result.env["DB_PASSWORD"] == DEFAULT_MASK
    assert result.env["API_KEY"] == DEFAULT_MASK
    assert result.env["AUTH_TOKEN"] == DEFAULT_MASK


def test_masked_count(base_env):
    result = mask_env(base_env)
    assert result.masked_count == 3


def test_masked_keys_list(base_env):
    result = mask_env(base_env)
    assert set(result.masked_keys) == {"DB_PASSWORD", "API_KEY", "AUTH_TOKEN"}


def test_show_length_encodes_value_length(base_env):
    result = mask_env(base_env, show_length=True)
    assert result.env["DB_PASSWORD"] == "*" * len("s3cr3t")
    assert result.env["API_KEY"] == "*" * len("abc123")


def test_custom_mask_string(base_env):
    result = mask_env(base_env, mask="[REDACTED]")
    assert result.env["DB_PASSWORD"] == "[REDACTED]"


def test_explicit_sensitive_keys_override_heuristic():
    env = {"MY_CUSTOM": "hidden", "DB_PASSWORD": "visible"}
    result = mask_env(env, sensitive_keys={"MY_CUSTOM"})
    assert result.env["MY_CUSTOM"] == DEFAULT_MASK
    # DB_PASSWORD is NOT in the explicit set, so it should be left alone
    assert result.env["DB_PASSWORD"] == "visible"


def test_empty_env_returns_empty_result():
    result = mask_env({})
    assert result.masked_count == 0
    assert result.env == {}


def test_summary_no_sensitive_keys():
    result = mask_env({"PORT": "3000", "HOST": "localhost"})
    assert result.summary() == "No sensitive keys detected."


def test_summary_with_masked_keys(base_env):
    result = mask_env(base_env)
    summary = result.summary()
    assert "3 key(s) masked" in summary


def test_was_masked_flag_set_correctly(base_env):
    result = mask_env(base_env)
    by_key = {e.key: e for e in result.entries}
    assert by_key["DB_PASSWORD"].was_masked is True
    assert by_key["APP_NAME"].was_masked is False


def test_to_dict_omits_original():
    result = mask_env({"SECRET_KEY": "abc"})
    d = result.entries[0].to_dict()
    assert "original" not in d
    assert d["key"] == "SECRET_KEY"
    assert d["was_masked"] is True
