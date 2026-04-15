"""Tests for envoy.extractor."""
import pytest
from envoy.extractor import extract_env, ExtractResult


@pytest.fixture()
def base_env() -> dict:
    return {
        "APP_NAME": "myapp",
        "APP_ENV": "production",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "SECRET_KEY": "s3cr3t",
        "DEBUG": "false",
    }


def test_extract_returns_extract_result(base_env):
    result = extract_env(base_env)
    assert isinstance(result, ExtractResult)


def test_no_keys_no_patterns_returns_all(base_env):
    result = extract_env(base_env)
    assert result.env == base_env
    assert result.extracted_count == len(base_env)
    assert result.excluded_count == 0


def test_exact_key_extracted(base_env):
    result = extract_env(base_env, keys=["APP_NAME"])
    assert "APP_NAME" in result.env
    assert result.extracted_count == 1


def test_exact_key_others_excluded(base_env):
    result = extract_env(base_env, keys=["DEBUG"])
    assert "DB_HOST" not in result.env
    assert "DB_HOST" in result.excluded_keys


def test_multiple_exact_keys(base_env):
    result = extract_env(base_env, keys=["DB_HOST", "DB_PORT"])
    assert set(result.env.keys()) == {"DB_HOST", "DB_PORT"}


def test_pattern_wildcard_matches_prefix(base_env):
    result = extract_env(base_env, patterns=["DB_*"])
    assert set(result.env.keys()) == {"DB_HOST", "DB_PORT"}


def test_pattern_question_mark_wildcard(base_env):
    # APP_ENV and APP_NAME both match APP_???
    result = extract_env(base_env, patterns=["APP_???"]) 
    # APP_ENV (7 chars after APP_) — fnmatch APP_??? matches exactly 3 chars
    assert "APP_ENV" in result.env
    assert "APP_NAME" not in result.env  # APP_NAME has 4 chars after APP_


def test_keys_and_patterns_combined(base_env):
    result = extract_env(base_env, keys=["SECRET_KEY"], patterns=["APP_*"])
    assert "SECRET_KEY" in result.env
    assert "APP_NAME" in result.env
    assert "APP_ENV" in result.env
    assert "DB_HOST" not in result.env


def test_matched_by_records_pattern(base_env):
    result = extract_env(base_env, patterns=["DB_*"])
    for entry in result.entries:
        assert entry.matched_by == "DB_*"


def test_matched_by_records_exact_key(base_env):
    result = extract_env(base_env, keys=["DEBUG"])
    assert result.entries[0].matched_by == "DEBUG"


def test_excluded_keys_sorted(base_env):
    result = extract_env(base_env, keys=["DEBUG"])
    assert result.excluded_keys == sorted(result.excluded_keys)


def test_summary_string(base_env):
    result = extract_env(base_env, keys=["DEBUG"])
    s = result.summary()
    assert "Extracted" in s
    assert "excluded" in s


def test_missing_key_not_in_result(base_env):
    result = extract_env(base_env, keys=["NONEXISTENT"])
    assert "NONEXISTENT" not in result.env
    assert result.extracted_count == 0
