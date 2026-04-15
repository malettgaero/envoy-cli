"""Promote env keys from one environment file to another with conflict detection."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PromoteEntry:
    key: str
    source_value: str
    target_value: Optional[str]  # None if key did not exist in target
    overwritten: bool

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "source_value": self.source_value,
            "target_value": self.target_value,
            "overwritten": self.overwritten,
        }


@dataclass
class PromoteResult:
    entries: List[PromoteEntry] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def promoted_count(self) -> int:
        return len(self.entries)

    @property
    def overwrite_count(self) -> int:
        return sum(1 for e in self.entries if e.overwritten)

    @property
    def new_count(self) -> int:
        return sum(1 for e in self.entries if not e.overwritten)

    def env(self) -> Dict[str, str]:
        """Return the merged target env after promotion."""
        return {e.key: e.source_value for e in self.entries}

    def summary(self) -> str:
        parts = [f"promoted={self.promoted_count}"]
        if self.overwrite_count:
            parts.append(f"overwritten={self.overwrite_count}")
        if self.new_count:
            parts.append(f"new={self.new_count}")
        if self.skipped:
            parts.append(f"skipped={len(self.skipped)}")
        return ", ".join(parts)


def promote_env(
    source: Dict[str, str],
    target: Dict[str, str],
    keys: Optional[List[str]] = None,
    overwrite: bool = True,
) -> PromoteResult:
    """Promote *keys* from *source* into *target*.

    Args:
        source:    The source environment (e.g. staging).
        target:    The target environment (e.g. production).
        keys:      Explicit list of keys to promote.  If None, all source keys
                   are promoted.
        overwrite: When False, keys already present in *target* are skipped.
    """
    result = PromoteResult()
    candidates = keys if keys is not None else list(source.keys())

    for key in candidates:
        if key not in source:
            result.skipped.append(key)
            continue

        source_value = source[key]
        target_value = target.get(key)
        already_exists = key in target

        if already_exists and not overwrite:
            result.skipped.append(key)
            continue

        result.entries.append(
            PromoteEntry(
                key=key,
                source_value=source_value,
                target_value=target_value,
                overwritten=already_exists,
            )
        )

    return result
