"""Clone keys from one env dict to new names, optionally removing originals."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CloneEntry:
    source_key: str
    target_key: str
    value: str
    removed_source: bool

    def to_dict(self) -> dict:
        return {
            "source_key": self.source_key,
            "target_key": self.target_key,
            "value": self.value,
            "removed_source": self.removed_source,
        }


@dataclass
class CloneResult:
    entries: List[CloneEntry] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    _env: Dict[str, str] = field(default_factory=dict, repr=False)

    @property
    def env(self) -> Dict[str, str]:
        return dict(self._env)

    @property
    def cloned_count(self) -> int:
        return len(self.entries)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped)

    def summary(self) -> str:
        parts = [f"{self.cloned_count} key(s) cloned"]
        if self.skipped_count:
            parts.append(f"{self.skipped_count} skipped (not found)")
        return ", ".join(parts)


def clone_env(
    env: Dict[str, str],
    mapping: Dict[str, str],
    *,
    move: bool = False,
    overwrite: bool = True,
) -> CloneResult:
    """Clone keys according to mapping {source: target}.

    Args:
        env: Source environment dict.
        mapping: Dict of {source_key: target_key}.
        move: If True, remove the source key after cloning.
        overwrite: If False, skip when target_key already exists.
    """
    result_env = dict(env)
    entries: List[CloneEntry] = []
    skipped: List[str] = []

    for src, tgt in mapping.items():
        if src not in env:
            skipped.append(src)
            continue
        if not overwrite and tgt in result_env:
            skipped.append(src)
            continue
        value = env[src]
        result_env[tgt] = value
        removed = False
        if move:
            result_env.pop(src, None)
            removed = True
        entries.append(CloneEntry(source_key=src, target_key=tgt, value=value, removed_source=removed))

    result = CloneResult(entries=entries, skipped=skipped)
    result._env = result_env
    return result
