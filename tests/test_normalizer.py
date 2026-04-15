"""Tests for envoy.normalizer."""
import pytest
from envoy.normalizer import normalize_env, NormalizeResult, NormalizeEntry


def _env(**kwargs: str):
    return dict(kwargs)


def test_normalize_returns_normalize_result():
    result = normalize_env({"key": "value"})
    assert isinstance(result, NormalizeResult)


def test_uppercase_keys_by_default():
    result = normalize_env({"db_host": "localhost"})
    assert "DB_HOST" in result.env


def test_uppercase_keys_disabled():
    result = normalize_env({"db_host": "localhost"}, uppercase_keys=False)
    assert "db_host" in result.env
    assert "DB_HOST" not in result.env


def test_strip_values_by_default():
    result = normalize_env({"KEY": "  value  "})
    assert result.env["KEY"] == "value"


def test_strip_values_disabled():
    result = normalize_env({"KEY": "  value  "}, strip_values=False)
    assert result.env["KEY"] == "  value  "


def test_spaces_in_keys_replaced_by_default():
    result = normalize_env({"my key": "val"})
    assert "MY_KEY" in result.env


def test_spaces_in_keys_replacement_char():
    result = normalize_env({"my key": "val"}, space_replacement="-", uppercase_keys=False)
    assert "my-key" in result.env


def test_spaces_in_keys_replacement_disabled():
    result = normalize_env({"my key": "val"}, replace_spaces_in_keys=False, uppercase_keys=False)
    assert "my key" in result.env


def test_changed_flag_true_when_key_uppercased():
    result = normalize_env({"key": "value"})
    assert result.changed is True


def test_changed_flag_false_when_already_normalized():
    result = normalize_env({"KEY": "value"})
    assert result.changed is False


def test_changed_count_correct():
    result = normalize_env({"key": "value", "OTHER": "  trimmed  "})
    # 'key' -> 'KEY' (key changed), 'OTHER' value trimmed
    assert result.changed_count == 2


def test_entry_has_original_key():
    result = normalize_env({"db_host": "localhost"})
    entry = result.entries[0]
    assert entry.original_key == "db_host"
    assert entry.key == "DB_HOST"


def test_entry_has_original_value():
    result = normalize_env({"KEY": "  hello  "})
    entry = result.entries[0]
    assert entry.original_value == "  hello  "
    assert entry.normalized_value == "hello"


def test_env_property_returns_normalized_dict():
    result = normalize_env({"a": "1", "b": "2"})
    assert result.env == {"A": "1", "B": "2"}


def test_summary_no_changes():
    result = normalize_env({"KEY": "val"})
    assert "already normalized" in result.summary()


def test_summary_with_changes():
    result = normalize_env({"key": "val"})
    assert "normalized" in result.summary()


def test_to_dict_includes_changed_flags():
    result = normalize_env({"key": "  val  "})
    d = result.entries[0].to_dict()
    assert d["key_changed"] is True
    assert d["value_changed"] is True


def test_empty_env_returns_empty_result():
    result = normalize_env({})
    assert result.entries == []
    assert result.changed is False
