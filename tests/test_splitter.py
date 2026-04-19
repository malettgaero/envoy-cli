"""Tests for envoy.splitter."""
import pytest
from envoy.splitter import split_env, SplitResult


@pytest.fixture()
def base_env():
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "REDIS_URL": "redis://localhost",
        "APP_NAME": "myapp",
        "SECRET_KEY": "s3cr3t",
    }


def test_split_returns_split_result(base_env):
    result = split_env(base_env, {"^DB_": "db.env"})
    assert isinstance(result, SplitResult)


def test_split_assigns_keys_to_correct_file(base_env):
    result = split_env(base_env, {"^DB_": "db.env", "^REDIS_": "redis.env"})
    assert "DB_HOST" in result.files["db.env"]
    assert "DB_PORT" in result.files["db.env"]
    assert "REDIS_URL" in result.files["redis.env"]


def test_unmatched_keys_collected(base_env):
    result = split_env(base_env, {"^DB_": "db.env"})
    assert "APP_NAME" in result.unmatched
    assert "SECRET_KEY" in result.unmatched
    assert "REDIS_URL" in result.unmatched


def test_default_file_captures_unmatched(base_env):
    result = split_env(base_env, {"^DB_": "db.env"}, default_file="other.env")
    assert len(result.unmatched) == 0
    assert "APP_NAME" in result.files["other.env"]
    assert "REDIS_URL" in result.files["other.env"]


def test_split_count_matches_unique_targets(base_env):
    result = split_env(
        base_env,
        {"^DB_": "db.env", "^REDIS_": "redis.env"},
        default_file="other.env",
    )
    assert result.split_count == 3


def test_strip_prefix_removes_prefix_from_key(base_env):
    result = split_env(
        base_env,
        {"^DB_": "db.env"},
        strip_prefix=True,
    )
    db_keys = list(result.files["db.env"].keys())
    assert "HOST" in db_keys
    assert "PORT" in db_keys


def test_strip_prefix_preserves_value(base_env):
    result = split_env(base_env, {"^DB_": "db.env"}, strip_prefix=True)
    assert result.files["db.env"]["HOST"] == "localhost"


def test_summary_contains_file_count(base_env):
    result = split_env(
        base_env,
        {"^DB_": "db.env", "^REDIS_": "redis.env"},
        default_file    )
    assert "3" in result.summary()


def test_summary_mentions_unmatched_when_present(base_env):
    result = split_env(base_env, {"^DB_": "db.env"})
    assert "unmatched" in result.summary()


def test_empty_env_returns_empty_result():
    result = split_env({}, {"^DB_": "db.env"})
    assert result.entries == []
    assert result.unmatched == []
    assert result.split_count == 0


def test_entry_to_dict_has_expected_keys(base_env):
    result = split_env(base_env, {"^DB_": "db.env"})
    entry = result.entries[0]
    d = entry.to_dict()
    assert set(d.keys()) == {"key", "value", "source_file", "target_file"}


def test_key_matched_by_first_matching_pattern(base_env):
    """When a key matches multiple patterns, it should be assigned to the first match."""
    result = split_env(
        base_env,
        {"^DB_": "db.env", "^DB_HOST": "override.env"},
    )
    assert "DB_HOST" in result.files["db.env"]
    assert "override.env" not in result.files
