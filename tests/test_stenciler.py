"""Tests for envoy.stenciler."""
import pytest
from envoy.stenciler import apply_stencil, StencilResult


@pytest.fixture()
def base_env():
    return {
        "APP_NAME": "myapp",
        "APP_ENV": "production",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "SECRET_KEY": "s3cr3t",
    }


def test_apply_stencil_returns_stencil_result(base_env):
    result = apply_stencil(base_env, ["APP_NAME"])
    assert isinstance(result, StencilResult)


def test_stencil_keeps_only_listed_keys(base_env):
    result = apply_stencil(base_env, ["APP_NAME", "DB_HOST"])
    assert set(result.env.keys()) == {"APP_NAME", "DB_HOST"}


def test_stencil_preserves_values(base_env):
    result = apply_stencil(base_env, ["SECRET_KEY"])
    assert result.env["SECRET_KEY"] == "s3cr3t"


def test_missing_key_recorded(base_env):
    result = apply_stencil(base_env, ["APP_NAME", "MISSING_KEY"])
    assert "MISSING_KEY" in result.missing_keys


def test_missing_key_not_in_env(base_env):
    result = apply_stencil(base_env, ["APP_NAME", "MISSING_KEY"])
    assert "MISSING_KEY" not in result.env


def test_dropped_keys_identified(base_env):
    result = apply_stencil(base_env, ["APP_NAME"])
    dropped = result.dropped_keys
    assert "DB_HOST" in dropped
    assert "SECRET_KEY" in dropped
    assert "APP_NAME" not in dropped


def test_passed_when_no_missing_keys(base_env):
    result = apply_stencil(base_env, ["APP_NAME", "DB_HOST"])
    assert result.passed is True


def test_failed_when_missing_keys(base_env):
    result = apply_stencil(base_env, ["APP_NAME", "NONEXISTENT"])
    assert result.passed is False


def test_entry_order_follows_stencil(base_env):
    stencil = ["SECRET_KEY", "APP_NAME", "DB_PORT"]
    result = apply_stencil(base_env, stencil)
    assert [e.key for e in result.entries] == stencil


def test_empty_stencil_returns_empty_env(base_env):
    result = apply_stencil(base_env, [])
    assert result.env == {}
    assert result.dropped_keys == list(base_env.keys())


def test_empty_source_all_missing():
    result = apply_stencil({}, ["APP_NAME", "DB_HOST"])
    assert result.missing_keys == ["APP_NAME", "DB_HOST"]
    assert result.passed is False


def test_summary_string(base_env):
    result = apply_stencil(base_env, ["APP_NAME", "MISSING"])
    s = result.summary()
    assert "kept" in s
    assert "missing" in s
    assert "dropped" in s


def test_to_dict_on_entry(base_env):
    result = apply_stencil(base_env, ["APP_NAME"])
    d = result.entries[0].to_dict()
    assert d["key"] == "APP_NAME"
    assert d["in_source"] is True
    assert d["in_stencil"] is True
