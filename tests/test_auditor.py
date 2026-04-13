"""Tests for envoy.auditor."""

import json
from pathlib import Path

import pytest

from envoy.auditor import AuditEntry, AuditLog


@pytest.fixture()
def log() -> AuditLog:
    return AuditLog()


def test_record_creates_entry(log):
    entry = log.record("set", "DB_HOST", ".env", old_value=None, new_value="localhost")
    assert isinstance(entry, AuditEntry)
    assert entry.action == "set"
    assert entry.key == "DB_HOST"
    assert entry.new_value == "localhost"
    assert len(log.entries) == 1


def test_record_appends_multiple(log):
    log.record("set", "A", ".env", new_value="1")
    log.record("delete", "B", ".env", old_value="2")
    assert len(log.entries) == 2


def test_entry_timestamp_is_iso(log):
    entry = log.record("set", "X", ".env")
    # Should not raise
    from datetime import datetime
    datetime.fromisoformat(entry.timestamp)


def test_save_and_load_roundtrip(tmp_path, log):
    log.record("set", "KEY", ".env", old_value=None, new_value="val")
    audit_file = tmp_path / "audit.json"
    log.save(audit_file)

    loaded = AuditLog.load(audit_file)
    assert len(loaded.entries) == 1
    assert loaded.entries[0].key == "KEY"
    assert loaded.entries[0].new_value == "val"


def test_save_appends_to_existing(tmp_path, log):
    audit_file = tmp_path / "audit.json"
    log.record("set", "FIRST", ".env")
    log.save(audit_file)

    log2 = AuditLog()
    log2.record("set", "SECOND", ".env")
    log2.save(audit_file)

    loaded = AuditLog.load(audit_file)
    assert len(loaded.entries) == 2
    keys = {e.key for e in loaded.entries}
    assert keys == {"FIRST", "SECOND"}


def test_load_missing_file_returns_empty(tmp_path):
    result = AuditLog.load(tmp_path / "nonexistent.json")
    assert result.entries == []


def test_filter_by_key(log):
    log.record("set", "A", ".env")
    log.record("set", "B", ".env")
    log.record("delete", "A", ".env")
    filtered = log.filter_by_key("A")
    assert len(filtered.entries) == 2
    assert all(e.key == "A" for e in filtered.entries)


def test_filter_by_action(log):
    log.record("set", "A", ".env")
    log.record("delete", "B", ".env")
    log.record("set", "C", ".env")
    filtered = log.filter_by_action("set")
    assert len(filtered.entries) == 2


def test_summary_empty(log):
    assert log.summary() == "No audit entries."


def test_summary_contains_key_and_action(log):
    log.record("set", "DB_URL", ".env", new_value="postgres://")
    s = log.summary()
    assert "DB_URL" in s
    assert "SET" in s
