"""Tests for envoy.exporter module."""

import json
import pytest

from envoy.exporter import ExportFormat, ExportError, export_env


@pytest.fixture()
def sample_env():
    return {"APP_ENV": "production", "DB_HOST": "localhost", "SECRET": 'p@ss"word'}


# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------

def test_export_json_is_valid_json(sample_env):
    result = export_env(sample_env, ExportFormat.JSON)
    parsed = json.loads(result)
    assert parsed == sample_env


def test_export_json_sorted_keys(sample_env):
    result = export_env(sample_env, ExportFormat.JSON)
    keys = list(json.loads(result).keys())
    assert keys == sorted(keys)


def test_export_json_empty_env():
    result = export_env({}, ExportFormat.JSON)
    assert json.loads(result) == {}


# ---------------------------------------------------------------------------
# Shell
# ---------------------------------------------------------------------------

def test_export_shell_format(sample_env):
    result = export_env(sample_env, ExportFormat.SHELL)
    lines = result.splitlines()
    assert all(line.startswith("export ") for line in lines)


def test_export_shell_sorted_keys(sample_env):
    result = export_env(sample_env, ExportFormat.SHELL)
    keys = [line.split("=")[0].replace("export ", "") for line in result.splitlines()]
    assert keys == sorted(keys)


def test_export_shell_escapes_double_quotes():
    env = {"MSG": 'say "hello"'}
    result = export_env(env, ExportFormat.SHELL)
    assert r'\"' in result


def test_export_shell_empty_env():
    result = export_env({}, ExportFormat.SHELL)
    assert result == ""


# ---------------------------------------------------------------------------
# Enum / error paths
# ---------------------------------------------------------------------------

def test_export_format_values():
    assert ExportFormat.JSON == "json"
    assert ExportFormat.YAML == "yaml"
    assert ExportFormat.SHELL == "shell"


def test_export_unsupported_format_raises():
    with pytest.raises(ExportError, match="Unsupported"):
        export_env({"K": "V"}, "xml")  # type: ignore[arg-type]
