"""CLI tests for the `envoy history` command."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envoy.cli import cli
from envoy.auditor import AuditLog


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def audit_file(tmp_path) -> Path:
    log = AuditLog()
    log.record("set", "DB_HOST", ".env", old_value=None, new_value="localhost")
    log.record("delete", "OLD_KEY", ".env", old_value="gone", new_value=None)
    log.record("set", "DB_PORT", ".env", new_value="5432")
    path = tmp_path / "audit.json"
    log.save(path)
    return path


def test_history_shows_all_entries(runner, audit_file):
    result = runner.invoke(cli, ["history", "--audit-file", str(audit_file)])
    assert result.exit_code == 0
    assert "DB_HOST" in result.output
    assert "OLD_KEY" in result.output
    assert "DB_PORT" in result.output


def test_history_filter_by_key(runner, audit_file):
    result = runner.invoke(
        cli, ["history", "--audit-file", str(audit_file), "--key", "DB_HOST"]
    )
    assert result.exit_code == 0
    assert "DB_HOST" in result.output
    assert "OLD_KEY" not in result.output


def test_history_filter_by_action(runner, audit_file):
    result = runner.invoke(
        cli, ["history", "--audit-file", str(audit_file), "--action", "delete"]
    )
    assert result.exit_code == 0
    assert "DELETE" in result.output.upper()
    assert "DB_HOST" not in result.output


def test_history_missing_audit_file(runner, tmp_path):
    result = runner.invoke(
        cli, ["history", "--audit-file", str(tmp_path / "nope.json")]
    )
    assert result.exit_code == 0
    assert "No audit entries" in result.output
