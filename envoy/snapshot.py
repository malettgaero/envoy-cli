"""Snapshot module: capture and restore .env file states."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from envoy.parser import parse_env_file, write_env_file


@dataclass
class Snapshot:
    label: str
    source: str
    timestamp: str
    env: Dict[str, str]

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "source": self.source,
            "timestamp": self.timestamp,
            "env": self.env,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        return cls(
            label=data["label"],
            source=data["source"],
            timestamp=data["timestamp"],
            env=data["env"],
        )


@dataclass
class SnapshotStore:
    path: Path
    _snapshots: List[Snapshot] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.path.exists():
            raw = json.loads(self.path.read_text())
            self._snapshots = [Snapshot.from_dict(d) for d in raw]

    def _save(self) -> None:
        self.path.write_text(json.dumps([s.to_dict() for s in self._snapshots], indent=2))

    def take(self, env_file: str, label: Optional[str] = None) -> Snapshot:
        env = parse_env_file(env_file)
        ts = datetime.now(timezone.utc).isoformat()
        snap = Snapshot(
            label=label or ts,
            source=env_file,
            timestamp=ts,
            env=env,
        )
        self._snapshots.append(snap)
        self._save()
        return snap

    def list_snapshots(self) -> List[Snapshot]:
        return list(self._snapshots)

    def get(self, label: str) -> Optional[Snapshot]:
        for snap in reversed(self._snapshots):
            if snap.label == label:
                return snap
        return None

    def restore(self, label: str, output_file: str) -> Snapshot:
        snap = self.get(label)
        if snap is None:
            raise KeyError(f"Snapshot '{label}' not found.")
        write_env_file(snap.env, output_file)
        return snap

    def delete(self, label: str) -> bool:
        before = len(self._snapshots)
        self._snapshots = [s for s in self._snapshots if s.label != label]
        if len(self._snapshots) < before:
            self._save()
            return True
        return False
