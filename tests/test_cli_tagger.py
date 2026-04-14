"""CLI tests for the tag command."""
import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envoy.cli_tagger import tag_cmd


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def tmp_env(tmp_path):
    p = tmp_path / ".env"
    p.write_text("APP_NAME=myapp\nDB_PASSWORD=secret\nAPI_KEY=abc\nDEBUG=true\n")
    return p


def test_apply_no_tags_lists_all_keys(runner, tmp_env):
    result = runner.invoke(tag_cmd, ["apply", str(tmp_env)])
    assert result.exit_code == 0
    assert "APP_NAME" in result.output
    assert "DB_PASSWORD" in result.output


def test_apply_tag_shown_in_output(runner, tmp_env):
    result = runner.invoke(
        tag_cmd,
        ["apply", str(tmp_env), "--tag", "DB_PASSWORD=secret"],
    )
    assert result.exit_code == 0
    assert "secret" in result.output


def test_filter_returns_only_matching_keys(runner, tmp_env):
    result = runner.invoke(
        tag_cmd,
        ["apply", str(tmp_env), "--tag", "DB_PASSWORD=secret", "--filter", "secret"],
    )
    assert result.exit_code == 0
    assert "DB_PASSWORD" in result.output
    assert "APP_NAME" not in result.output


def test_filter_no_match_reports_no_keys(runner, tmp_env):
    result = runner.invoke(
        tag_cmd,
        ["apply", str(tmp_env), "--filter", "nonexistent"],
    )
    assert result.exit_code == 0
    assert "No matching keys" in result.output


def test_json_output_is_valid(runner, tmp_env):
    result = runner.invoke(
        tag_cmd,
        ["apply", str(tmp_env), "--tag", "API_KEY=external", "--json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    keys = [d["key"] for d in data]
    assert "API_KEY" in keys


def test_invalid_tag_format_raises_error(runner, tmp_env):
    result = runner.invoke(tag_cmd, ["apply", str(tmp_env), "--tag", "BADFORMAT"])
    assert result.exit_code != 0


def test_summary_line_present(runner, tmp_env):
    result = runner.invoke(
        tag_cmd,
        ["apply", str(tmp_env), "--tag", "DEBUG=feature-flag"],
    )
    assert result.exit_code == 0
    assert "tagged" in result.output
