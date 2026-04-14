"""Tests for envoy.pinner."""
import pytest

from envoy.pinner import PinResult, PinViolation, pin_env


@pytest.fixture()
def base_env() -> dict:
    return {
        "APP_ENV": "production",
        "LOG_LEVEL": "info",
        "RETRY_COUNT": "3",
    }


def test_all_pins_match_passes(base_env):
    result = pin_env(base_env, {"APP_ENV": "production", "LOG_LEVEL": "info"})
    assert result.passed
    assert result.checked == 2
    assert result.violations == []


def test_wrong_value_flagged(base_env):
    result = pin_env(base_env, {"APP_ENV": "staging"})
    assert not result.passed
    assert len(result.violations) == 1
    v = result.violations[0]
    assert v.key == "APP_ENV"
    assert v.pinned == "staging"
    assert v.actual == "production"


def test_missing_key_flagged(base_env):
    result = pin_env(base_env, {"MISSING_KEY": "value"})
    assert not result.passed
    v = result.violations[0]
    assert v.key == "MISSING_KEY"
    assert v.actual is None


def test_multiple_violations_collected(base_env):
    result = pin_env(
        base_env,
        {"APP_ENV": "staging", "LOG_LEVEL": "debug", "RETRY_COUNT": "3"},
    )
    assert not result.passed
    assert result.checked == 3
    assert len(result.violations) == 2
    keys = {v.key for v in result.violations}
    assert keys == {"APP_ENV", "LOG_LEVEL"}


def test_empty_pins_always_passes(base_env):
    result = pin_env(base_env, {})
    assert result.passed
    assert result.checked == 0


def test_empty_env_with_pins_fails():
    result = pin_env({}, {"APP_ENV": "production"})
    assert not result.passed
    assert result.violations[0].actual is None


def test_summary_on_pass(base_env):
    result = pin_env(base_env, {"APP_ENV": "production"})
    assert "1 pinned key(s) match" in result.summary()


def test_summary_on_failure(base_env):
    result = pin_env(base_env, {"APP_ENV": "staging"})
    summary = result.summary()
    assert "violation" in summary
    assert "APP_ENV" in summary


def test_violation_str_missing_key():
    v = PinViolation(key="FOO", pinned="bar", actual=None)
    assert "missing" in str(v)


def test_violation_str_wrong_value():
    v = PinViolation(key="FOO", pinned="bar", actual="baz")
    assert "bar" in str(v)
    assert "baz" in str(v)


def test_violation_to_dict():
    v = PinViolation(key="K", pinned="p", actual="a")
    d = v.to_dict()
    assert d == {"key": "K", "pinned": "p", "actual": "a"}
