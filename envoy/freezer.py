"""Freeze an env file — mark it read-only and record a checksum so tampering can be detected."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


@dataclass
class FreezeViolation:
    key: str
    reason: str

    def to_dict(self) -> dict:
        return {"key": self.key, "reason": self.reason}


@dataclass
class FreezeResult:
    checksum: str
    env: Dict[str, str]
    violations: list[FreezeViolation] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.violations) == 0

    def summary(self) -> str:
        if self.passed:
            return f"OK — checksum {self.checksum[:12]}"
        lines = [f"TAMPERED — {len(self.violations)} violation(s):"]
        for v in self.violations:
            lines.append(f"  {v.key}: {v.reason}")
        return "\n".join(lines)


def _checksum(env: Dict[str, str]) -> str:
    payload = json.dumps(env, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def freeze_env(env: Dict[str, str]) -> FreezeResult:
    """Produce a FreezeResult containing a checksum of the current env."""
    cs = _checksum(env)
    return FreezeResult(checksum=cs, env=dict(env))


def verify_env(env: Dict[str, str], checksum: str) -> FreezeResult:
    """Verify *env* against a previously recorded *checksum*."""
    current = _checksum(env)
    violations: list[FreezeViolation] = []
    if current != checksum:
        violations.append(
            FreezeViolation(key="__env__", reason=f"checksum mismatch (expected {checksum[:12]}, got {current[:12]})")
        )
    return FreezeResult(checksum=current, env=dict(env), violations=violations)


def save_freeze(result: FreezeResult, path: Path) -> None:
    path.write_text(json.dumps({"checksum": result.checksum}, indent=2))


def load_checksum(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return data.get("checksum")
