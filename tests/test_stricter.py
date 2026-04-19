import pytest
from envoy.stricter import strict_check, StrictResult, StrictViolation


@pytest.fixture
def base_env():
    return {
        "APP_NAME": "myapp",
        "DB_HOST": "localhost",
        "SECRET_KEY": "abc123",
    }


def test_strict_returns_strict_result(base_env):
    result = strict_check(base_env)
    assert isinstance(result, StrictResult)


def test_clean_env_passes(base_env):
    result = strict_check(base_env)
    assert result.passed()
    assert result.checked == 3


def test_lowercase_key_flagged():
    result = strict_check({"app_name": "value"})
    assert not result.passed()
    assert any(v.key == "app_name" for v in result.violations)


def test_mixed_case_key_flagged():
    result = strict_check({"AppName": "value"})
    assert not result.passed()


def test_uppercase_check_disabled():
    result = strict_check({"app_name": "value"}, require_uppercase=False)
    assert result.passed()


def test_empty_value_flagged(base_env):
    base_env["EMPTY_KEY"] = ""
    result = strict_check(base_env)
    assert not result.passed()
    assert any(v.key == "EMPTY_KEY" for v in result.violations)


def test_blank_value_flagged():
    result = strict_check({"MY_KEY": "   "})
    assert not result.passed()


def test_empty_disallowed_disabled():
    result = strict_check({"MY_KEY": ""}, disallow_empty=False)
    assert result.passed()


def test_max_value_length_exceeded():
    result = strict_check({"MY_KEY": "toolongvalue"}, max_value_length=5)
    assert not result.passed()
    assert any("max length" in v.reason for v in result.violations)


def test_max_value_length_ok():
    result = strict_check({"MY_KEY": "ok"}, max_value_length=10)
    assert result.passed()


def test_forbidden_pattern_flagged():
    result = strict_check({"MY_KEY": "password123"}, forbidden_patterns=[r"password"])
    assert not result.passed()
    assert any("forbidden pattern" in v.reason for v in result.violations)


def test_forbidden_pattern_not_matched():
    result = strict_check({"MY_KEY": "safe_value"}, forbidden_patterns=[r"password"])
    assert result.passed()


def test_summary_on_pass(base_env):
    result = strict_check(base_env)
    assert "passed" in result.summary()


def test_summary_on_fail():
    result = strict_check({"bad_key": ""})
    assert "violation" in result.summary()


def test_violation_to_dict():
    v = StrictViolation(key="X", reason="bad")
    d = v.to_dict()
    assert d["key"] == "X"
    assert d["reason"] == "bad"


def test_violation_str():
    v = StrictViolation(key="X", reason="bad")
    assert "X" in str(v)
    assert "bad" in str(v)
