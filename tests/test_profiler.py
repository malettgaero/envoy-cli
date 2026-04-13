"""Tests for envoy.profiler."""
import pytest
from envoy.profiler import compare_profile, ProfileResult, ProfileViolation


@pytest.fixture()
def base_env():
    return {
        "APP_ENV": "production",
        "DATABASE_URL": "postgres://localhost/db",
        "SECRET_KEY": "s3cr3t",
        "DEBUG": "false",
    }


def test_all_match_passes(base_env):
    profile = {
        "APP_ENV": "production",
        "DEBUG": "false",
    }
    result = compare_profile(base_env, profile, profile_name="prod")
    assert result.passed
    assert result.profile == "prod"


def test_wildcard_accepts_any_non_empty_value(base_env):
    profile = {"SECRET_KEY": "*", "DATABASE_URL": "*"}
    result = compare_profile(base_env, profile)
    assert result.passed


def test_wildcard_rejects_empty_value():
    env = {"API_KEY": ""}
    profile = {"API_KEY": "*"}
    result = compare_profile(env, profile)
    assert not result.passed
    assert result.violations[0].reason == "key present but value is empty"


def test_missing_key_flagged(base_env):
    profile = {"MISSING_KEY": "*"}
    result = compare_profile(base_env, profile)
    assert not result.passed
    assert result.violations[0].key == "MISSING_KEY"
    assert result.violations[0].reason == "key missing from env"


def test_value_mismatch_flagged(base_env):
    profile = {"APP_ENV": "staging"}
    result = compare_profile(base_env, profile)
    assert not result.passed
    v = result.violations[0]
    assert v.key == "APP_ENV"
    assert v.expected == "staging"
    assert v.actual == "production"
    assert v.reason == "value mismatch"


def test_strict_mode_flags_extra_keys(base_env):
    profile = {"APP_ENV": "production"}
    result = compare_profile(base_env, profile, strict=True)
    assert not result.passed
    extra_keys = {v.key for v in result.violations}
    assert "DATABASE_URL" in extra_keys
    assert "SECRET_KEY" in extra_keys
    assert "DEBUG" in extra_keys


def test_strict_mode_no_extras_passes():
    env = {"APP_ENV": "production"}
    profile = {"APP_ENV": "production"}
    result = compare_profile(env, profile, strict=True)
    assert result.passed


def test_summary_passed(base_env):
    profile = {"APP_ENV": "production"}
    result = compare_profile(base_env, profile, profile_name="prod")
    assert "passed" in result.summary()


def test_summary_violations():
    env = {"APP_ENV": "dev"}
    profile = {"APP_ENV": "production", "MISSING": "*"}
    result = compare_profile(env, profile, profile_name="prod")
    summary = result.summary()
    assert "2 violation" in summary
    assert "APP_ENV" in summary
    assert "MISSING" in summary


def test_to_dict_shape():
    v = ProfileViolation("KEY", "expected", "actual", "value mismatch")
    d = v.to_dict()
    assert set(d.keys()) == {"key", "expected", "actual", "reason"}
