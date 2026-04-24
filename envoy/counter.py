"""Count and report statistics about keys in a .env file."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class CountEntry:
    category: str
    count: int
    keys: List[str]

    def to_dict(self) -> dict:
        return {"category": self.category, "count": self.count, "keys": self.keys}


@dataclass
class CountResult:
    entries: List[CountEntry]
    total: int
    _by_category: Dict[str, CountEntry] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        self._by_category = {e.category: e for e in self.entries}

    def count_for(self, category: str) -> int:
        entry = self._by_category.get(category)
        return entry.count if entry else 0

    def summary(self) -> str:
        lines = [f"Total keys: {self.total}"]
        for entry in self.entries:
            lines.append(f"  {entry.category}: {entry.count}")
        return "\n".join(lines)


_SECRET_PATTERNS = ("password", "secret", "token", "key", "api", "auth", "private")


def _classify(key: str, value: str) -> str:
    lower = key.lower()
    if any(p in lower for p in _SECRET_PATTERNS):
        return "secret"
    if value == "":
        return "empty"
    return "plain"


def count_env(env: Dict[str, str]) -> CountResult:
    """Count keys in *env* grouped by category."""
    buckets: Dict[str, List[str]] = {"secret": [], "empty": [], "plain": []}

    for key, value in env.items():
        cat = _classify(key, value)
        buckets[cat].append(key)

    entries = [
        CountEntry(category=cat, count=len(keys), keys=sorted(keys))
        for cat, keys in buckets.items()
        if keys
    ]
    entries.sort(key=lambda e: e.category)
    total = sum(e.count for e in entries)
    return CountResult(entries=entries, total=total)
