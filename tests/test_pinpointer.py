import pytest
from envoy.pinpointer import pinpoint_env, PinpointEntry, PinpointResult


@pytest.fixture
def sources():
    return {
        ".env.dev": {"DB_HOST": "localhost", "DEBUG": "true", "API_KEY": "dev-key"},
        ".env.prod": {"DB_HOST": "prod.db", "API_KEY": "prod-key", "LOG_LEVEL": "warn"},
        ".env.test": {"DB_HOST": "localhost", "DEBUG": "false"},
    }


def test_pinpoint_returns_result(sources):
    result = pinpoint_env(["DB_HOST"], sources)
    assert isinstance(result, PinpointResult)


def test_searched_files_recorded(sources):
    result = pinpoint_env(["DB_HOST"], sources)
    assert set(result.searched_files) == set(sources.keys())


def test_key_found_in_all_sources(sources):
    result = pinpoint_env(["DB_HOST"], sources)
    entry = result.get("DB_HOST")
    assert entry is not None
    assert set(entry.sources) == {".env.dev", ".env.prod", ".env.test"}


def test_key_found_in_single_source(sources):
    result = pinpoint_env(["LOG_LEVEL"], sources)
    entry = result.get("LOG_LEVEL")
    assert entry is not None
    assert entry.sources == [".env.prod"]
    assert entry.is_unique


def test_missing_key_not_in_entries(sources):
    result = pinpoint_env(["MISSING_KEY"], sources)
    assert result.get("MISSING_KEY") is None
    assert "MISSING_KEY" not in result.found_keys


def test_consistent_key_detected(sources):
    # DB_HOST is 'localhost' in dev and test, 'prod.db' in prod -> inconsistent
    result = pinpoint_env(["DB_HOST"], sources)
    entry = result.get("DB_HOST")
    assert not entry.is_consistent


def test_unique_and_consistent_key(sources):
    result = pinpoint_env(["LOG_LEVEL"], sources)
    entry = result.get("LOG_LEVEL")
    assert entry.is_unique
    assert entry.is_consistent


def test_multiple_keys_in_one_call(sources):
    result = pinpoint_env(["DEBUG", "API_KEY", "LOG_LEVEL"], sources)
    assert set(result.found_keys) == {"API_KEY", "DEBUG", "LOG_LEVEL"}


def test_entries_sorted_alphabetically(sources):
    result = pinpoint_env(["LOG_LEVEL", "API_KEY", "DEBUG"], sources)
    assert result.found_keys == sorted(result.found_keys)


def test_values_recorded_per_source(sources):
    result = pinpoint_env(["API_KEY"], sources)
    entry = result.get("API_KEY")
    assert entry.values[".env.dev"] == "dev-key"
    assert entry.values[".env.prod"] == "prod-key"


def test_to_dict_structure(sources):
    result = pinpoint_env(["DEBUG"], sources)
    entry = result.get("DEBUG")
    d = entry.to_dict()
    assert "key" in d and "sources" in d and "values" in d


def test_summary_contains_key_name(sources):
    result = pinpoint_env(["DB_HOST"], sources)
    s = result.summary()
    assert "DB_HOST" in s
    assert "Searched" in s
