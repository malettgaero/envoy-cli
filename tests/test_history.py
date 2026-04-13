"""Tests for envoy.history integration helpers."""

from pathlib import Path

import pytest

from envoy.diff import diff_envs
from envoy.history import record_diff, record_merge, show_history
from envoy.merger import merge_envs, Strategy
from envoy.auditor import AuditLog


@pytest.fixture()
def audit_file(tmp_path) -> Path:
    return tmp_path / "audit.json"


def test_record_diff_added_key(audit_file):
    diff = diff_envs({}, {"NEW_KEY": "hello"}, mask_secrets=False)
    log = record_diff(diff, ".env.new", audit_path=audit_file, persist=False)
    assert any(e.key == "NEW_KEY" and e.action == "set" for e in log.entries)


def test_record_diff_removed_key(audit_file):
    diff = diff_envs({"OLD_KEY": "bye"}, {}, mask_secrets=False)
    log = record_diff(diff, ".env", audit_path=audit_file, persist=False)
    assert any(e.key == "OLD_KEY" and e.action == "delete" for e in log.entries)


def test_record_diff_changed_key(audit_file):
    diff = diff_envs({"HOST": "old"}, {"HOST": "new"}, mask_secrets=False)
    log = record_diff(diff, ".env", audit_path=audit_file, persist=False)
    entry = next(e for e in log.entries if e.key == "HOST")
    assert entry.old_value == "old"
    assert entry.new_value == "new"


def test_record_diff_persists(audit_file):
    diff = diff_envs({}, {"PERSIST_KEY": "yes"}, mask_secrets=False)
    record_diff(diff, ".env", audit_path=audit_file, persist=True)
    loaded = AuditLog.load(audit_file)
    assert any(e.key == "PERSIST_KEY" for e in loaded.entries)


def test_record_diff_no_changes_empty_log(audit_file):
    diff = diff_envs({"A": "1"}, {"A": "1"}, mask_secrets=False)
    log = record_diff(diff, ".env", audit_path=audit_file, persist=False)
    assert log.entries == []


def test_record_merge_logs_all_keys(audit_file):
    result = merge_envs([{"A": "1", "B": "2"}], strategy=Strategy.LAST_WINS)
    log = record_merge(result, source_label="merged", audit_path=audit_file, persist=False)
    keys = {e.key for e in log.entries}
    assert {"A", "B"}.issubset(keys)
    assert all(e.action == "merge" for e in log.entries)


def test_show_history_returns_summary(audit_file):
    diff = diff_envs({}, {"SHOW_KEY": "val"}, mask_secrets=False)
    record_diff(diff, ".env", audit_path=audit_file, persist=True)
    output = show_history(audit_path=audit_file)
    assert "SHOW_KEY" in output


def test_show_history_filtered_by_key(audit_file):
    diff = diff_envs({}, {"KEY_A": "1", "KEY_B": "2"}, mask_secrets=False)
    record_diff(diff, ".env", audit_path=audit_file, persist=True)
    output = show_history(audit_path=audit_file, key="KEY_A")
    assert "KEY_A" in output
    assert "KEY_B" not in output


def test_show_history_missing_file(tmp_path):
    output = show_history(audit_path=tmp_path / "missing.json")
    assert output == "No audit entries."
