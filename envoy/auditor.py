"""Audit trail for .env file changes — tracks who changed what and when."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class AuditEntry:
    timestamp: str
    action: str          # 'set', 'delete', 'merge', 'validate'
    key: str
    old_value: Optional[str]
    new_value: Optional[str]
    source_file: str
    author: str = field(default_factory=lambda: os.environ.get("USER", "unknown"))

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AuditLog:
    entries: List[AuditEntry] = field(default_factory=list)

    def record(self, action: str, key: str, source_file: str,
               old_value: Optional[str] = None,
               new_value: Optional[str] = None) -> AuditEntry:
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            action=action,
            key=key,
            old_value=old_value,
            new_value=new_value,
            source_file=source_file,
        )
        self.entries.append(entry)
        return entry

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        existing: list = []
        if path.exists():
            with path.open() as fh:
                existing = json.load(fh)
        existing.extend(e.to_dict() for e in self.entries)
        with path.open("w") as fh:
            json.dump(existing, fh, indent=2)

    @staticmethod
    def load(path: Path) -> "AuditLog":
        path = Path(path)
        if not path.exists():
            return AuditLog()
        with path.open() as fh:
            raw = json.load(fh)
        entries = [AuditEntry(**e) for e in raw]
        return AuditLog(entries=entries)

    def filter_by_key(self, key: str) -> "AuditLog":
        return AuditLog(entries=[e for e in self.entries if e.key == key])

    def filter_by_action(self, action: str) -> "AuditLog":
        return AuditLog(entries=[e for e in self.entries if e.action == action])

    def summary(self) -> str:
        if not self.entries:
            return "No audit entries."
        lines = []
        for e in self.entries:
            old = f"{e.old_value!r}" if e.old_value is not None else "—"
            new = f"{e.new_value!r}" if e.new_value is not None else "—"
            lines.append(
                f"[{e.timestamp}] {e.action.upper():8s} {e.key} "
                f"({old} → {new}) in {e.source_file} by {e.author}"
            )
        return "\n".join(lines)
