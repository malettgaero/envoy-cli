import pytest
from envoy.summarizer import summarize_env, SummaryResult, SummaryEntry


@pytest.fixture
def base_env():
    return {
        "DB_HOST": "localhost",
        "DB_PASSWORD": "secret123",
        "API_KEY": "abc",
        "FEATURE_FLAG": "true",
        "APP_URL": "http://example.com",
        "EMPTY_VAL": "",
    }


def test_summarize_returns_summary_result(base_env):
    result = summarize_env(base_env)
    assert isinstance(result, SummaryResult)


def test_total_count(base_env):
    result = summarize_env(base_env)
    assert result.total == len(base_env)


def test_empty_count(base_env):
    result = summarize_env(base_env)
    assert result.empty_count == 1


def test_secret_count(base_env):
    result = summarize_env(base_env)
    # DB_PASSWORD and API_KEY should be flagged
    assert result.secret_count >= 2


def test_entries_sorted_alphabetically(base_env):
    result = summarize_env(base_env)
    keys = [e.key for e in result.entries]
    assert keys == sorted(keys)


def test_categories_populated(base_env):
    result = summarize_env(base_env)
    assert isinstance(result.categories, dict)
    assert sum(result.categories.values()) == result.total


def test_database_category_detected(base_env):
    result = summarize_env(base_env)
    cats = {e.key: e.category for e in result.entries}
    assert cats["DB_HOST"] == "database"


def test_network_category_detected(base_env):
    result = summarize_env(base_env)
    cats = {e.key: e.category for e in result.entries}
    assert cats["APP_URL"] == "network"


def test_feature_category_detected(base_env):
    result = summarize_env(base_env)
    cats = {e.key: e.category for e in result.entries}
    assert cats["FEATURE_FLAG"] == "feature"


def test_empty_env_returns_zero_counts():
    result = summarize_env({})
    assert result.total == 0
    assert result.empty_count == 0
    assert result.secret_count == 0
    assert result.categories == {}


def test_overview_contains_total(base_env):
    result = summarize_env(base_env)
    overview = result.overview()
    assert "Total keys" in overview
    assert str(result.total) in overview


def test_to_dict_on_entry(base_env):
    result = summarize_env(base_env)
    d = result.entries[0].to_dict()
    assert "key" in d
    assert "value_length" in d
    assert "is_empty" in d
    assert "is_secret" in d
    assert "category" in d


def test_value_length_recorded():
    env = {"MY_KEY": "hello"}
    result = summarize_env(env)
    assert result.entries[0].value_length == 5
