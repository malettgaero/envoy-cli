"""Tests for envoy.tokenizer."""
import pytest
from envoy.tokenizer import (
    tokenize_env,
    TOKEN_LITERAL,
    TOKEN_SECRET,
    TOKEN_REFERENCE,
)


@pytest.fixture
def base_env():
    return {
        "APP_NAME": "myapp",
        "DB_PASSWORD": "s3cr3t",
        "DB_HOST": "${HOST}",
        "GREETING": "hello $USER",
        "API_KEY": "key-${ENV}-value",
    }


def test_tokenize_returns_result(base_env):
    result = tokenize_env(base_env)
    assert result is not None
    assert len(result.entries) == len(base_env)


def test_plain_literal_token(base_env):
    result = tokenize_env(base_env)
    entry = result.for_key("APP_NAME")
    assert entry is not None
    assert len(entry.tokens) == 1
    assert entry.tokens[0].kind == TOKEN_LITERAL
    assert entry.tokens[0].value == "myapp"


def test_secret_key_produces_secret_token():
    result = tokenize_env({"DB_PASSWORD": "hunter2"})
    entry = result.for_key("DB_PASSWORD")
    assert entry.tokens[0].kind == TOKEN_SECRET


def test_reference_only_value():
    result = tokenize_env({"DB_HOST": "${HOST}"})
    entry = result.for_key("DB_HOST")
    assert len(entry.tokens) == 1
    assert entry.tokens[0].kind == TOKEN_REFERENCE
    assert entry.tokens[0].value == "HOST"


def test_bare_dollar_reference():
    result = tokenize_env({"GREETING": "hello $USER"})
    entry = result.for_key("GREETING")
    kinds = [t.kind for t in entry.tokens]
    assert TOKEN_REFERENCE in kinds
    ref = next(t for t in entry.tokens if t.kind == TOKEN_REFERENCE)
    assert ref.value == "USER"


def test_mixed_literal_and_reference():
    result = tokenize_env({"API_KEY": "key-${ENV}-value"})
    entry = result.for_key("API_KEY")
    kinds = [t.kind for t in entry.tokens]
    assert TOKEN_REFERENCE in kinds
    assert TOKEN_LITERAL in kinds or TOKEN_SECRET in kinds


def test_sensitive_keys_list(base_env):
    result = tokenize_env(base_env)
    sensitive = result.sensitive_keys
    assert "DB_PASSWORD" in sensitive
    assert "API_KEY" in sensitive
    assert "APP_NAME" not in sensitive


def test_reference_keys_list(base_env):
    result = tokenize_env(base_env)
    refs = result.reference_keys
    assert "DB_HOST" in refs
    assert "GREETING" in refs
    assert "APP_NAME" not in refs


def test_to_dict_structure():
    result = tokenize_env({"HOST": "localhost"})
    d = result.entries[0].to_dict()
    assert "key" in d
    assert "raw_value" in d
    assert "tokens" in d
    assert isinstance(d["tokens"], list)


def test_empty_env_returns_empty_result():
    result = tokenize_env({})
    assert result.entries == []
    assert result.sensitive_keys == []
    assert result.reference_keys == []
