import pytest
from envoy.labeler import label_env, LabelResult, LabelEntry


@pytest.fixture
def base_env():
    return {
        "DB_HOST": "localhost",
        "DB_PASSWORD": "secret",
        "APP_NAME": "myapp",
        "AWS_SECRET_KEY": "abc123",
        "PORT": "8080",
    }


def test_label_env_returns_label_result(base_env):
    result = label_env(base_env)
    assert isinstance(result, LabelResult)


def test_all_keys_present(base_env):
    result = label_env(base_env)
    assert {e.key for e in result.entries} == set(base_env.keys())


def test_entries_sorted_alphabetically(base_env):
    result = label_env(base_env)
    keys = [e.key for e in result.entries]
    assert keys == sorted(keys)


def test_no_label_map_all_unlabeled(base_env):
    result = label_env(base_env)
    for entry in result.entries:
        assert entry.labels == []


def test_exact_key_label_applied(base_env):
    result = label_env(base_env, label_map={"database": ["DB_HOST", "DB_PASSWORD"]})
    assert "database" in result.labels_for_key("DB_HOST")
    assert "database" in result.labels_for_key("DB_PASSWORD")
    assert "database" not in result.labels_for_key("PORT")


def test_wildcard_pattern_matches(base_env):
    result = label_env(base_env, label_map={"aws": ["AWS_*"]})
    assert "aws" in result.labels_for_key("AWS_SECRET_KEY")
    assert "aws" not in result.labels_for_key("DB_HOST")


def test_keys_for_label(base_env):
    result = label_env(base_env, label_map={"db": ["DB_*"]})
    db_keys = result.keys_for_label("db")
    assert "DB_HOST" in db_keys
    assert "DB_PASSWORD" in db_keys
    assert "PORT" not in db_keys


def test_multiple_labels_on_same_key(base_env):
    result = label_env(
        base_env,
        label_map={"sensitive": ["DB_PASSWORD", "AWS_SECRET_KEY"], "db": ["DB_*"]},
    )
    labels = result.labels_for_key("DB_PASSWORD")
    assert "sensitive" in labels
    assert "db" in labels


def test_all_labels_returns_sorted_unique(base_env):
    result = label_env(
        base_env,
        label_map={"db": ["DB_*"], "aws": ["AWS_*"], "sensitive": ["DB_PASSWORD"]},
    )
    all_labels = result.all_labels()
    assert all_labels == sorted(set(all_labels))
    assert "db" in all_labels
    assert "aws" in all_labels


def test_env_output_matches_input(base_env):
    result = label_env(base_env, label_map={"x": ["PORT"]})
    assert result.env() == base_env


def test_missing_label_returns_empty_list(base_env):
    result = label_env(base_env)
    assert result.keys_for_label("nonexistent") == []


def test_labels_for_missing_key_returns_empty(base_env):
    result = label_env(base_env)
    assert result.labels_for_key("DOES_NOT_EXIST") == []
