"""Tests for envoy.flattener."""
import pytest
from envoy.flattener import flatten_env, unflatten_env, FlattenResult


@pytest.fixture()
def base_env():
    return {
        "DB.HOST": "localhost",
        "DB.PORT": "5432",
        "APP_NAME": "myapp",
        "CACHE.REDIS.URL": "redis://localhost",
    }


def test_flatten_returns_flatten_result(base_env):
    result = flatten_env(base_env)
    assert isinstance(result, FlattenResult)


def test_dot_keys_converted_to_double_underscore(base_env):
    result = flatten_env(base_env)
    env = result.env
    assert "DB__HOST" in env
    assert "DB__PORT" in env


def test_non_dot_key_unchanged(base_env):
    result = flatten_env(base_env)
    assert "APP_NAME" in result.env
    assert result.env["APP_NAME"] == "myapp"


def test_nested_dot_key_fully_replaced(base_env):
    result = flatten_env(base_env)
    assert "CACHE__REDIS__URL" in result.env
    assert result.env["CACHE__REDIS__URL"] == "redis://localhost"


def test_values_preserved(base_env):
    result = flatten_env(base_env)
    assert result.env["DB__HOST"] == "localhost"
    assert result.env["DB__PORT"] == "5432"


def test_changed_count_correct(base_env):
    result = flatten_env(base_env)
    # DB.HOST, DB.PORT, CACHE.REDIS.URL => 3 changed
    assert result.changed_count == 3


def test_no_dots_means_no_changes():
    env = {"KEY_ONE": "a", "KEY_TWO": "b"}
    result = flatten_env(env)
    assert result.changed_count == 0


def test_summary_no_changes():
    env = {"PLAIN": "value"}
    result = flatten_env(env)
    assert "no changes" in result.summary()


def test_summary_with_changes(base_env):
    result = flatten_env(base_env)
    assert "flattened" in result.summary()


def test_custom_separator():
    env = {"DB.HOST": "localhost"}
    result = flatten_env(env, separator="-")
    assert "DB-HOST" in result.env


def test_custom_source_sep():
    env = {"DB/HOST": "localhost"}
    result = flatten_env(env, separator="__", source_sep="/")
    assert "DB__HOST" in result.env


def test_unflatten_reverses_flatten():
    env = {"DB__HOST": "localhost", "APP_NAME": "myapp"}
    unflat = unflatten_env(env)
    assert "DB.HOST" in unflat
    assert "APP_NAME" in unflat


def test_unflatten_custom_separator():
    env = {"DB-HOST": "localhost"}
    unflat = unflatten_env(env, separator="-", target_sep=".")
    assert "DB.HOST" in unflat


def test_roundtrip(base_env):
    flat = flatten_env(base_env).env
    restored = unflatten_env(flat)
    assert restored == base_env
