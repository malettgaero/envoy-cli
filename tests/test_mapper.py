"""Tests for envoy.mapper."""
import pytest
from envoy.mapper import map_envs, MapEntry, MapResult


@pytest.fixture()
def sources():
    return {
        ".env.dev": {"DB_HOST": "localhost", "DB_PORT": "5432", "DEBUG": "true"},
        ".env.prod": {"DB_HOST": "prod.db", "DB_PORT": "5432", "SECRET_KEY": "abc"},
        ".env.test": {"DB_HOST": "testhost", "DEBUG": "false"},
    }


def test_map_envs_returns_map_result(sources):
    result = map_envs(sources)
    assert isinstance(result, MapResult)


def test_all_keys_collected(sources):
    result = map_envs(sources)
    assert set(result.all_keys) == {"DB_HOST", "DB_PORT", "DEBUG", "SECRET_KEY"}


def test_keys_sorted_alphabetically(sources):
    result = map_envs(sources)
    assert result.all_keys == sorted(result.all_keys, key=str.lower)


def test_source_files_recorded(sources):
    result = map_envs(sources)
    assert set(result.source_files) == set(sources.keys())


def test_consistent_key_detected(sources):
    result = map_envs(sources)
    entry = result.entry_for("DB_PORT")
    assert entry is not None
    assert entry.is_consistent is True


def test_inconsistent_key_detected(sources):
    result = map_envs(sources)
    entry = result.entry_for("DB_HOST")
    assert entry is not None
    assert entry.is_consistent is False


def test_inconsistent_keys_list(sources):
    result = map_envs(sources)
    assert "DB_HOST" in result.inconsistent_keys
    assert "DB_PORT" not in result.inconsistent_keys


def test_unique_to_one_file(sources):
    result = map_envs(sources)
    assert "SECRET_KEY" in result.unique_to_one_file
    assert "DB_HOST" not in result.unique_to_one_file


def test_entry_for_missing_key_returns_none(sources):
    result = map_envs(sources)
    assert result.entry_for("NONEXISTENT") is None


def test_entry_files_list(sources):
    result = map_envs(sources)
    entry = result.entry_for("DEBUG")
    assert set(entry.files) == {".env.dev", ".env.test"}


def test_entry_values_dict(sources):
    result = map_envs(sources)
    entry = result.entry_for("DB_HOST")
    assert entry.values[".env.dev"] == "localhost"
    assert entry.values[".env.prod"] == "prod.db"


def test_file_count(sources):
    result = map_envs(sources)
    assert result.entry_for("DB_HOST").file_count == 3
    assert result.entry_for("SECRET_KEY").file_count == 1


def test_to_dict(sources):
    result = map_envs(sources)
    d = result.entry_for("DB_PORT").to_dict()
    assert d["key"] == "DB_PORT"
    assert isinstance(d["files"], list)
    assert isinstance(d["values"], dict)


def test_summary_contains_counts(sources):
    result = map_envs(sources)
    s = result.summary()
    assert "4" in s  # total keys
    assert "3" in s  # source files


def test_empty_sources_returns_empty_result():
    result = map_envs({})
    assert result.entries == []
    assert result.source_files == []
