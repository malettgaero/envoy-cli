"""Key renaming support for .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class RenameEntry:
    old_key: str
    new_key: str
    value: str
    skipped: bool = False
    skip_reason: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "old_key": self.old_key,
            "new_key": self.new_key,
            "value": self.value,
            "skipped": self.skipped,
            "skip_reason": self.skip_reason,
        }


@dataclass
class RenameResult:
    env: Dict[str, str]
    entries: List[RenameEntry] = field(default_factory=list)

    @property
    def renamed_count(self) -> int:
        return sum(1 for e in self.entries if not e.skipped)

    @property
    def skipped_count(self) -> int:
        return sum(1 for e in self.entries if e.skipped)

    def summary(self) -> str:
        lines = [f"Renamed: {self.renamed_count}, Skipped: {self.skipped_count}"]
        for e in self.entries:
            if e.skipped:
                lines.append(f"  SKIP  {e.old_key} -> {e.new_key}: {e.skip_reason}")
            else:
                lines.append(f"  OK    {e.old_key} -> {e.new_key}")
        return "\n".join(lines)


def rename_keys(
    env: Dict[str, str],
    renames: Dict[str, str],
    overwrite: bool = False,
) -> RenameResult:
    """Rename keys in *env* according to the *renames* mapping.

    Parameters
    ----------
    env:       Source environment dictionary.
    renames:   Mapping of {old_key: new_key}.
    overwrite: When True, silently replace an existing key at the destination.
               When False (default), skip the rename and record the reason.
    """
    result = dict(env)
    entries: List[RenameEntry] = []

    for old_key, new_key in renames.items():
        if old_key not in result:
            entries.append(
                RenameEntry(
                    old_key=old_key,
                    new_key=new_key,
                    value="",
                    skipped=True,
                    skip_reason="source key not found",
                )
            )
            continue

        if new_key in result and not overwrite:
            entries.append(
                RenameEntry(
                    old_key=old_key,
                    new_key=new_key,
                    value=result[old_key],
                    skipped=True,
                    skip_reason=f"destination key '{new_key}' already exists",
                )
            )
            continue

        value = result.pop(old_key)
        result[new_key] = value
        entries.append(RenameEntry(old_key=old_key, new_key=new_key, value=value))

    return RenameResult(env=result, entries=entries)
