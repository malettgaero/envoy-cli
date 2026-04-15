"""Tests for envoy.classifier."""
import pytest
from envoy.classifier import classify_env, ClassifyEntry, ClassifyResult, _classify_key


@pytest.fixture
def base_env():
    return {
        "DB_HOST": "localhost",
        "DB_PASSWORD": "s3cr3t",
        "API_KEY": "abc123",
        "APP_PORT": "8080",
        "LOG_LEVEL": "info",
        "ENABLE_FEATURE_X": "true",
        "AUTH_TOKEN": "tok",
        "S3_BUCKET": "my-bucket",
        "SMTP_HOST": "mail.example.com",
        "APP_NAME": "myapp",
    }


def test_classify_env_returns_classify_result(base_env):
    result = classify_env(base_env)
    assert isinstance(result, ClassifyResult)


def test_all_keys_present(base_env):
    result = classify_env(base_env)
    keys = {e.key for e in result.entries}
    assert keys == set(base_env.keys())


def test_entries_sorted_alphabetically(base_env):
    result = classify_env(base_env)
    keys = [e.key for e in result.entries]
    assert keys == sorted(keys)


def test_secret_category_detected():
    result = classify_env({"DB_PASSWORD": "x", "API_KEY": "y", "JWT_SECRET": "z"})
    for entry in result.entries:
        assert entry.category == "secret", f"{entry.key} should be 'secret'"


def test_database_category_detected():
    assert _classify_key("POSTGRES_URL") == "database"
    assert _classify_key("REDIS_HOST") == "database"


def test_network_category_detected():
    assert _classify_key("APP_PORT") == "network"
    assert _classify_key("SERVICE_URL") == "network"


def test_feature_flag_category_detected():
    assert _classify_key("ENABLE_FEATURE_X") == "feature"
    assert _classify_key("DISABLE_CACHE") == "feature"


def test_logging_category_detected():
    assert _classify_key("LOG_LEVEL") == "logging"
    assert _classify_key("DEBUG") == "logging"


def test_auth_category_detected():
    assert _classify_key("AUTH_TOKEN") == "auth"
    assert _classify_key("OAUTH_CLIENT_ID") == "auth"


def test_storage_category_detected():
    assert _classify_key("S3_BUCKET") == "storage"
    assert _classify_key("UPLOAD_PATH") == "storage"


def test_email_category_detected():
    assert _classify_key("SMTP_HOST") == "email"
    assert _classify_key("SENDGRID_API") == "email"


def test_general_fallback():
    assert _classify_key("APP_NAME") == "general"
    assert _classify_key("VERSION") == "general"


def test_by_category_groups_correctly(base_env):
    result = classify_env(base_env)
    groups = result.by_category()
    assert isinstance(groups, dict)
    assert "database" in groups or "secret" in groups
    for cat, items in groups.items():
        assert all(e.category == cat for e in items)


def test_category_for_known_key(base_env):
    result = classify_env(base_env)
    assert result.category_for("LOG_LEVEL") == "logging"


def test_category_for_unknown_key_returns_none(base_env):
    result = classify_env(base_env)
    assert result.category_for("NONEXISTENT") is None


def test_summary_contains_category_names(base_env):
    result = classify_env(base_env)
    summary = result.summary()
    assert "general" in summary or "secret" in summary


def test_empty_env_returns_empty_result():
    result = classify_env({})
    assert result.entries == []
    assert result.summary() == "No keys to classify."
