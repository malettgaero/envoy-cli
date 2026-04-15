"""Pruner: remove keys from an env dict that match a given set of patterns."""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from typing import Dict, List, Sequence


@dataclass
class PruneEntry:
    key: str
    value: str
    reason: str  # 'exact' | 'pattern'

    def to_dict(self) -> dict:
        return {"key": self.key, "value": self.value, "reason": self.reason}


@dataclass
class PruneResult:
    original: Dict[str, str]
    pruned: List[PruneEntry] = field(default_factory=list)
    kept: Dict[str, str] = field(default_factory=dict)

    @property
    def pruned_count(self) -> int:
        return len(self.pruned)

    @property
    def changed(self) -> bool:
        return self.pruned_count > 0

    def summary(self) -> str:
        if not self.changed:
            return "No keys pruned."
        lines = [f"Pruned {self.pruned_count} key(s):"]
        for e in self.pruned:
            lines.append(f"  - {e.key}  ({e.reason})")
        return "\n".join(lines)


def prune_env(
    env: Dict[str, str],
    keys: Sequence[str] = (),
    patterns: Sequence[str] = (),
) -> PruneResult:
    """Return a PruneResult with matching keys removed.

    Args:
        env:      The source environment mapping.
        keys:     Exact key names to remove.
        patterns: Glob-style patterns (fnmatch) to match against key names.
    """
    exact_set = set(keys)
    pruned: List[PruneEntry] = []
    kept: Dict[str, str] = {}

    for k, v in env.items():
        if k in exact_set:
            pruned.append(PruneEntry(key=k, value=v, reason="exact"))
            continue
        matched_pattern = next(
            (p for p in patterns if fnmatch.fnmatch(k, p)), None
        )
        if matched_pattern is not None:
            pruned.append(PruneEntry(key=k, value=v, reason=f"pattern:{matched_pattern}"))
            continue
        kept[k] = v

    return PruneResult(original=dict(env), pruned=pruned, kept=kept)
