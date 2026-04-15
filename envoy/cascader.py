"""Cascade multiple .env files, with later files overriding earlier ones.

Cascading differs from merging in that it is purely ordered/layered:
base → staging → local, each layer overrides the previous silently.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class CascadeEntry:
    key: str
    value: str
    source: str          # path of the file that won
    overridden_by: Optional[str] = None   # for entries that were overridden

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "source": self.source,
            "overridden_by": self.overridden_by,
        }


@dataclass
class CascadeResult:
    entries: List[CascadeEntry] = field(default_factory=list)
    # entries that were shadowed (key appeared in an earlier layer)
    shadowed: List[CascadeEntry] = field(default_factory=list)

    @property
    def env(self) -> Dict[str, str]:
        return {e.key: e.value for e in self.entries}

    @property
    def override_count(self) -> int:
        return len(self.shadowed)

    def summary(self) -> str:
        lines = [f"Cascaded {len(self.entries)} key(s)"]
        if self.shadowed:
            lines.append(f"{self.override_count} key(s) overridden by a later layer")
        return "; ".join(lines)


def cascade_envs(
    sources: List[Tuple[str, Dict[str, str]]],
) -> CascadeResult:
    """Cascade a list of (name, env_dict) pairs left-to-right.

    The rightmost source wins for any given key.

    Args:
        sources: ordered list of (label, mapping) tuples, base first.

    Returns:
        CascadeResult with winning entries and shadowed entries.
    """
    if not sources:
        return CascadeResult()

    # key -> (value, source_label)
    current: Dict[str, Tuple[str, str]] = {}
    shadowed: List[CascadeEntry] = []

    for label, env in sources:
        for key, value in env.items():
            if key in current:
                old_value, old_source = current[key]
                shadowed.append(
                    CascadeEntry(
                        key=key,
                        value=old_value,
                        source=old_source,
                        overridden_by=label,
                    )
                )
            current[key] = (value, label)

    entries = [
        CascadeEntry(key=k, value=v, source=src)
        for k, (v, src) in sorted(current.items())
    ]
    return CascadeResult(entries=entries, shadowed=shadowed)
