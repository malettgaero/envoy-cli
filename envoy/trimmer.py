"""Trimmer: detect and remove trailing whitespace from .env values."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class TrimEntry:
    key: str
    original: str
    trimmed: str

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "original": repr(self.original),
            "trimmed": repr(self.trimmed),
        }


@dataclass
class TrimResult:
    env: Dict[str, str]
    entries: List[TrimEntry] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return len(self.entries) > 0

    @property
    def changed_count(self) -> int:
        return len(self.entries)

    def summary(self) -> str:
        if not self.changed:
            return "No trailing whitespace found."
        lines = [f"{len(self.entries)} key(s) trimmed:"]
        for e in self.entries:
            lines.append(f"  {e.key}: {repr(e.original)} -> {repr(e.trimmed)}")
        return "\n".join(lines)


def trim_env(env: Dict[str, str]) -> TrimResult:
    """Strip leading/trailing whitespace from all values in *env*.

    Returns a :class:`TrimResult` whose ``.env`` contains the cleaned
    mapping and ``.entries`` lists every key that was actually changed.
    """
    cleaned: Dict[str, str] = {}
    entries: List[TrimEntry] = []

    for key, value in env.items():
        trimmed = value.strip()
        cleaned[key] = trimmed
        if trimmed != value:
            entries.append(TrimEntry(key=key, original=value, trimmed=trimmed))

    return TrimResult(env=cleaned, entries=entries)
