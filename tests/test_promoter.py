"""Tests for envoy.promoter."""
import pytest
from envoy.promoter import promote_env, PromoteResult, PromoteEntry


@pytest.fixture
def base_env():
    return {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET": "abc"}


@pytest.fixture
def target_env():
    return {"DB_HOST": "prod-host", "API_KEY": "xyz"}


def test_promote_all_keys_from_source(base_env, target_env):
    result = promote_env(base_env, target_env)
    assert isinstance(result, PromoteResult)
    assert result.promoted_count == len(base_env)


def test_promote_specific_keys(base_env, target_env):
    result = promote_env(base_env, target_env, keys=["DB_HOST", "SECRET"])
    promoted_keys = [e.key for e in result.entries]
    assert "DB_HOST" in promoted_keys
    assert "SECRET" in promoted_keys
    assert "DB_PORT" not in promoted_keys


def test_missing_key_in_source_goes_to_skipped(base_env, target_env):
    result = promote_env(base_env, target_env, keys=["MISSING_KEY"])
    assert "MISSING_KEY" in result.skipped
    assert result.promoted_count == 0


def test_overwrite_true_replaces_existing_key(base_env, target_env):
    result = promote_env(base_env, target_env, keys=["DB_HOST"], overwrite=True)
    entry = result.entries[0]
    assert entry.key == "DB_HOST"
    assert entry.source_value == "localhost"
    assert entry.target_value == "prod-host"
    assert entry.overwritten is True


def test_overwrite_false_skips_existing_key(base_env, target_env):
    result = promote_env(base_env, target_env, keys=["DB_HOST"], overwrite=False)
    assert "DB_HOST" in result.skipped
    assert result.promoted_count == 0


def test_new_key_not_in_target_is_not_overwrite(base_env, target_env):
    result = promote_env(base_env, target_env, keys=["SECRET"])
    entry = result.entries[0]
    assert entry.overwritten is False
    assert entry.target_value is None


def test_env_method_returns_promoted_values(base_env, target_env):
    result = promote_env(base_env, target_env, keys=["DB_HOST", "SECRET"])
    env = result.env()
    assert env["DB_HOST"] == "localhost"
    assert env["SECRET"] == "abc"


def test_summary_contains_counts(base_env, target_env):
    result = promote_env(base_env, target_env)
    s = result.summary()
    assert "promoted=" in s


def test_overwrite_count_and_new_count(base_env, target_env):
    result = promote_env(base_env, target_env, overwrite=True)
    # DB_HOST exists in target → overwritten; DB_PORT and SECRET are new
    assert result.overwrite_count == 1
    assert result.new_count == 2


def test_to_dict_has_expected_keys(base_env, target_env):
    result = promote_env(base_env, target_env, keys=["DB_HOST"])
    d = result.entries[0].to_dict()
    assert set(d.keys()) == {"key", "source_value", "target_value", "overwritten"}
