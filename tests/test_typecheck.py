"""Tests for envoy.typecheck module."""

import pytest
from envoy.typecheck import typecheck_env, TypeCheckResult, TypeViolation


@pytest.fixture
def base_env():
    return {
        "PORT": "8080",
        "RATE": "1.5",
        "DEBUG": "true",
        "APP_URL": "https://example.com",
        "CONTACT": "admin@example.com",
        "NAME": "myapp",
    }


def test_all_valid_types_pass(base_env):
    hints = {
        "PORT": "int",
        "RATE": "float",
        "DEBUG": "bool",
        "APP_URL": "url",
        "CONTACT": "email",
        "NAME": "str",
    }
    result = typecheck_env(base_env, hints)
    assert result.passed
    assert result.violations == []


def test_invalid_int_flagged():
    env = {"PORT": "not_a_number"}
    result = typecheck_env(env, {"PORT": "int"})
    assert not result.passed
    assert len(result.violations) == 1
    assert result.violations[0].key == "PORT"
    assert result.violations[0].expected_type == "int"


def test_invalid_float_flagged():
    env = {"RATE": "abc"}
    result = typecheck_env(env, {"RATE": "float"})
    assert not result.passed
    assert "not a valid float" in result.violations[0].message


def test_invalid_bool_flagged():
    env = {"DEBUG": "maybe"}
    result = typecheck_env(env, {"DEBUG": "bool"})
    assert not result.passed
    assert result.violations[0].expected_type == "bool"


def test_valid_bool_variants_pass():
    for val in ["true", "false", "1", "0", "yes", "no", "on", "off",
                "True", "FALSE", "YES"]:
        env = {"FLAG": val}
        result = typecheck_env(env, {"FLAG": "bool"})
        assert result.passed, f"Expected {val!r} to be valid bool"


def test_invalid_url_flagged():
    env = {"APP_URL": "not-a-url"}
    result = typecheck_env(env, {"APP_URL": "url"})
    assert not result.passed
    assert "not a valid URL" in result.violations[0].message


def test_valid_url_passes():
    env = {"APP_URL": "https://api.example.org/v1"}
    result = typecheck_env(env, {"APP_URL": "url"})
    assert result.passed


def test_invalid_email_flagged():
    env = {"CONTACT": "not-an-email"}
    result = typecheck_env(env, {"CONTACT": "email"})
    assert not result.passed
    assert "not a valid email" in result.violations[0].message


def test_missing_key_in_env_is_skipped():
    env = {"OTHER": "value"}
    result = typecheck_env(env, {"PORT": "int"})
    assert result.passed


def test_unknown_type_recorded():
    env = {"FOO": "bar"}
    result = typecheck_env(env, {"FOO": "uuid"})
    assert result.passed
    assert "uuid" in result.unknown_types


def test_summary_on_clean():
    result = TypeCheckResult()
    assert "All values match" in result.summary()


def test_summary_on_violations():
    v = TypeViolation("PORT", "abc", "int", "'abc' is not a valid integer")
    result = TypeCheckResult(violations=[v])
    summary = result.summary()
    assert "1 type violation" in summary
    assert "PORT" in summary


def test_to_dict_shape():
    v = TypeViolation("X", "bad", "int", "not int")
    d = v.to_dict()
    assert set(d.keys()) == {"key", "value", "expected_type", "message"}
