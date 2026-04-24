"""Tests for envoy.injector."""
import pytest
from envoy.injector import inject_env, InjectEntry, InjectResult


@pytest.fixture
def base_env():
    return {"APP_HOST": "localhost", "APP_PORT": "8080", "DEBUG": "false"}


@pytest.fixture
def source_env():
    return {"APP_PORT": "9090", "SECRET_KEY": "abc123", "NEW_VAR": "hello"}


def test_inject_returns_inject_result(base_env, source_env):
    result = inject_env(base_env, source_env)
    assert isinstance(result, InjectResult)


def test_inject_all_keys_from_source(base_env, source_env):
    result = inject_env(base_env, source_env)
    assert result.injected_count == 3


def test_inject_env_contains_new_key(base_env, source_env):
    result = inject_env(base_env, source_env)
    assert result.env["SECRET_KEY"] == "abc123"
    assert result.env["NEW_VAR"] == "hello"


def test_inject_overwrites_existing_key(base_env, source_env):
    result = inject_env(base_env, source_env)
    assert result.env["APP_PORT"] == "9090"


def test_inject_overwritten_flag_set(base_env, source_env):
    result = inject_env(base_env, source_env)
    overwritten = [e for e in result.entries if e.overwritten]
    assert len(overwritten) == 1
    assert overwritten[0].key == "APP_PORT"


def test_inject_no_overwrite_skips_existing(base_env, source_env):
    result = inject_env(base_env, source_env, overwrite=False)
    assert result.env["APP_PORT"] == "8080"


def test_inject_no_overwrite_still_adds_new_keys(base_env, source_env):
    result = inject_env(base_env, source_env, overwrite=False)
    assert "SECRET_KEY" in result.env
    assert "NEW_VAR" in result.env


def test_inject_specific_keys_only(base_env, source_env):
    result = inject_env(base_env, source_env, keys=["SECRET_KEY"])
    assert result.injected_count == 1
    assert result.env["SECRET_KEY"] == "abc123"
    assert result.env["APP_PORT"] == "8080"  # not overwritten


def test_inject_missing_key_in_source_is_skipped(base_env):
    result = inject_env(base_env, {"X": "1"}, keys=["MISSING", "X"])
    assert result.injected_count == 1
    assert result.env["X"] == "1"


def test_inject_source_label_stored(base_env, source_env):
    result = inject_env(base_env, source_env, source_label=".env.prod")
    for entry in result.entries:
        assert entry.source == ".env.prod"


def test_inject_base_env_not_mutated(base_env, source_env):
    original = dict(base_env)
    inject_env(base_env, source_env)
    assert base_env == original


def test_inject_overwritten_count(base_env, source_env):
    result = inject_env(base_env, source_env)
    assert result.overwritten_count == 1


def test_inject_summary_string(base_env, source_env):
    result = inject_env(base_env, source_env)
    s = result.summary()
    assert "injected" in s
    assert "overwritten" in s


def test_entry_to_dict(base_env, source_env):
    result = inject_env(base_env, source_env, source_label="src")
    d = result.entries[0].to_dict()
    assert "key" in d
    assert "value" in d
    assert "overwritten" in d
    assert "source" in d


def test_inject_empty_source(base_env):
    result = inject_env(base_env, {})
    assert result.injected_count == 0
    assert result.env == base_env
