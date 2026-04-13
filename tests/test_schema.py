"""Tests for envoy.schema module."""
import pytest
from envoy.schema import (
    SchemaField,
    SchemaResult,
    SchemaViolation,
    validate_schema,
    load_schema_from_dict,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _schema(*fields: SchemaField):
    return list(fields)


# ---------------------------------------------------------------------------
# validate_schema
# ---------------------------------------------------------------------------

def test_valid_env_passes():
    schema = _schema(SchemaField(key="APP_ENV"), SchemaField(key="PORT"))
    result = validate_schema({"APP_ENV": "production", "PORT": "8080"}, schema)
    assert result.is_valid


def test_missing_required_key_flagged():
    schema = _schema(SchemaField(key="SECRET_KEY", required=True))
    result = validate_schema({}, schema)
    assert not result.is_valid
    assert any(v.key == "SECRET_KEY" for v in result.violations)


def test_missing_optional_key_passes():
    schema = _schema(SchemaField(key="DEBUG", required=False))
    result = validate_schema({}, schema)
    assert result.is_valid


def test_allowed_values_passes():
    schema = _schema(SchemaField(key="LOG_LEVEL", allowed_values=["debug", "info", "warn", "error"]))
    result = validate_schema({"LOG_LEVEL": "info"}, schema)
    assert result.is_valid


def test_disallowed_value_flagged():
    schema = _schema(SchemaField(key="LOG_LEVEL", allowed_values=["debug", "info"]))
    result = validate_schema({"LOG_LEVEL": "verbose"}, schema)
    assert not result.is_valid
    assert any("allowed values" in v.reason for v in result.violations)


def test_pattern_match_passes():
    schema = _schema(SchemaField(key="PORT", pattern=r"\d{4,5}"))
    result = validate_schema({"PORT": "8080"}, schema)
    assert result.is_valid


def test_pattern_mismatch_flagged():
    schema = _schema(SchemaField(key="PORT", pattern=r"\d{4,5}"))
    result = validate_schema({"PORT": "abc"}, schema)
    assert not result.is_valid
    assert any("pattern" in v.reason for v in result.violations)


def test_multiple_violations_collected():
    schema = _schema(
        SchemaField(key="A", required=True),
        SchemaField(key="B", pattern=r"\d+"),
    )
    result = validate_schema({"B": "not-a-number"}, schema)
    assert len(result.violations) == 2


def test_summary_on_failure_lists_issues():
    schema = _schema(SchemaField(key="MISSING", required=True))
    result = validate_schema({}, schema)
    summary = result.summary()
    assert "MISSING" in summary
    assert "failed" in summary


def test_summary_on_success():
    result = SchemaResult()
    assert "passed" in result.summary()


# ---------------------------------------------------------------------------
# load_schema_from_dict
# ---------------------------------------------------------------------------

def test_load_schema_from_dict_basic():
    raw = {
        "APP_ENV": {"required": True, "allowed_values": ["dev", "prod"]},
        "PORT": {"required": False, "pattern": r"\d+", "description": "HTTP port"},
    }
    fields = load_schema_from_dict(raw)
    assert len(fields) == 2
    keys = {f.key for f in fields}
    assert keys == {"APP_ENV", "PORT"}


def test_load_schema_defaults():
    raw = {"MY_KEY": {}}
    fields = load_schema_from_dict(raw)
    assert fields[0].required is True
    assert fields[0].pattern is None
    assert fields[0].allowed_values is None
