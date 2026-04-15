"""Key rotation support: rename keys according to a rotation map and optionally redact old values."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class RotateEntry:
    old_key: str
    new_key: str
    value: str
    skipped: bool = False
    skip_reason: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "old_key": self.old_key,
            "new_key": self.new_key,
            "value": self.value if not self.skipped else None,
            "skipped": self.skipped,
            "skip_reason": self.skip_reason,
        }


@dataclass
class RotateResult:
    entries: List[RotateEntry] = field(default_factory=list)
    _env: Dict[str, str] = field(default_factory=dict, repr=False)

    @property
    def rotated_count(self) -> int:
        return sum(1 for e in self.entries if not e.skipped)

    @property
    def skipped_count(self) -> int:
        return sum(1 for e in self.entries if e.skipped)

    @property
    def env(self) -> Dict[str, str]:
        return dict(self._env)

    def summary(self) -> str:
        lines = [f"Rotated {self.rotated_count} key(s), skipped {self.skipped_count}."]
        for e in self.entries:
            if e.skipped:
                lines.append(f"  SKIP  {e.old_key} -> {e.new_key}: {e.skip_reason}")
            else:
                lines.append(f"  OK    {e.old_key} -> {e.new_key}")
        return "\n".join(lines)


def rotate_env(
    env: Dict[str, str],
    rotation_map: Dict[str, str],
    keep_old: bool = False,
    allow_overwrite: bool = False,
) -> RotateResult:
    """Rotate keys in *env* according to *rotation_map* {old_key: new_key}.

    Args:
        env: Source environment dict.
        rotation_map: Mapping of old key names to new key names.
        keep_old: If True, retain the old key alongside the new one.
        allow_overwrite: If True, overwrite an existing new_key; otherwise skip.

    Returns:
        RotateResult with the updated env and per-entry details.
    """
    result_env: Dict[str, str] = dict(env)
    entries: List[RotateEntry] = []

    for old_key, new_key in rotation_map.items():
        if old_key not in env:
            entries.append(
                RotateEntry(old_key, new_key, "", skipped=True, skip_reason="key not found")
            )
            continue

        if new_key in result_env and not allow_overwrite:
            entries.append(
                RotateEntry(
                    old_key, new_key, env[old_key],
                    skipped=True,
                    skip_reason=f"new key '{new_key}' already exists",
                )
            )
            continue

        value = result_env.pop(old_key) if not keep_old else result_env[old_key]
        result_env[new_key] = value
        entries.append(RotateEntry(old_key, new_key, value))

    return RotateResult(entries=entries, _env=result_env)
