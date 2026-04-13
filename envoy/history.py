"""High-level history helpers: build an AuditLog from a diff or merge result."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from envoy.auditor import AuditLog
from envoy.diff import DiffResult
from envoy.merger import MergeResult

_DEFAULT_AUDIT_FILE = Path(".envoy_audit.json")


def record_diff(
    diff: DiffResult,
    source_file: str,
    audit_path: Path = _DEFAULT_AUDIT_FILE,
    persist: bool = True,
) -> AuditLog:
    """Record every change detected in a DiffResult to the audit log."""
    log = AuditLog()
    for key in diff.added:
        log.record("set", key, source_file, old_value=None, new_value=diff.b.get(key))
    for key in diff.removed:
        log.record("delete", key, source_file, old_value=diff.a.get(key), new_value=None)
    for key in diff.changed:
        log.record(
            "set", key, source_file,
            old_value=diff.a.get(key),
            new_value=diff.b.get(key),
        )
    if persist and log.entries:
        log.save(audit_path)
    return log


def record_merge(
    result: MergeResult,
    source_label: str = "merge",
    audit_path: Path = _DEFAULT_AUDIT_FILE,
    persist: bool = True,
) -> AuditLog:
    """Record the merged key/value pairs as 'merge' actions in the audit log."""
    log = AuditLog()
    for key, value in result.env.items():
        log.record("merge", key, source_label, new_value=value)
    if persist and log.entries:
        log.save(audit_path)
    return log


def show_history(
    audit_path: Path = _DEFAULT_AUDIT_FILE,
    key: Optional[str] = None,
    action: Optional[str] = None,
) -> str:
    """Return a formatted history string, optionally filtered."""
    log = AuditLog.load(audit_path)
    if key:
        log = log.filter_by_key(key)
    if action:
        log = log.filter_by_action(action)
    return log.summary()
