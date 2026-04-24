"""Anchor support: pin specific keys to required positions (top/bottom/group)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class AnchorEntry:
    key: str
    value: str
    position: str  # 'top', 'bottom', 'group', 'free'
    group: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "position": self.position,
            "group": self.group,
        }


@dataclass
class AnchorResult:
    entries: List[AnchorEntry] = field(default_factory=list)
    order: List[str] = field(default_factory=list)

    @property
    def env(self) -> Dict[str, str]:
        return {e.key: e.value for e in self.entries}

    @property
    def changed(self) -> bool:
        original = [e.key for e in self.entries]
        return original != self.order

    def summary(self) -> str:
        top = [e.key for e in self.entries if e.position == "top"]
        bottom = [e.key for e in self.entries if e.position == "bottom"]
        free = [e.key for e in self.entries if e.position == "free"]
        parts = []
        if top:
            parts.append(f"{len(top)} anchored top")
        if bottom:
            parts.append(f"{len(bottom)} anchored bottom")
        if free:
            parts.append(f"{len(free)} free")
        return ", ".join(parts) if parts else "no keys"


def anchor_env(
    env: Dict[str, str],
    top_keys: Optional[List[str]] = None,
    bottom_keys: Optional[List[str]] = None,
    groups: Optional[Dict[str, List[str]]] = None,
) -> AnchorResult:
    """Reorder env keys so that top_keys come first and bottom_keys come last."""
    top_keys = top_keys or []
    bottom_keys = bottom_keys or []
    groups = groups or {}

    group_lookup: Dict[str, str] = {}
    for group_name, keys in groups.items():
        for k in keys:
            group_lookup[k] = group_name

    def _position(k: str) -> str:
        if k in top_keys:
            return "top"
        if k in bottom_keys:
            return "bottom"
        if k in group_lookup:
            return "group"
        return "free"

    top = [k for k in top_keys if k in env]
    bottom = [k for k in bottom_keys if k in env]
    top_set = set(top)
    bottom_set = set(bottom)

    middle_free = [k for k in env if k not in top_set and k not in bottom_set]
    ordered_keys = top + middle_free + bottom

    entries = [
        AnchorEntry(
            key=k,
            value=env[k],
            position=_position(k),
            group=group_lookup.get(k),
        )
        for k in ordered_keys
    ]

    result = AnchorResult(entries=entries, order=ordered_keys)
    return result
