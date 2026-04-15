"""Deduplicator: remove duplicate keys from an env dict, keeping first or last occurrence."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple


class KeepStrategy(str, Enum):
    FIRST = "first"
    LAST = "last"


@dataclass
class DeduplicateEntry:
    key: str
    kept_value: str
    dropped_values: List[str]
    occurrences: int

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "kept_value": self.kept_value,
            "dropped_values": self.dropped_values,
            "occurrences": self.occurrences,
        }


@dataclass
class DeduplicateResult:
    entries: List[DeduplicateEntry] = field(default_factory=list)
    clean_env: Dict[str, str] = field(default_factory=dict)

    @property
    def duplicate_count(self) -> int:
        return len(self.entries)

    @property
    def has_duplicates(self) -> bool:
        return self.duplicate_count > 0

    def summary(self) -> str:
        if not self.has_duplicates:
            return "No duplicate keys found."
        lines = [f"{self.duplicate_count} duplicate key(s) removed:"]
        for e in self.entries:
            lines.append(
                f"  {e.key}: kept '{e.kept_value}', "
                f"dropped {e.dropped_values} ({e.occurrences} total occurrences)"
            )
        return "\n".join(lines)


def deduplicate_env(
    pairs: List[Tuple[str, str]],
    strategy: KeepStrategy = KeepStrategy.FIRST,
) -> DeduplicateResult:
    """Deduplicate a list of (key, value) pairs.

    Args:
        pairs: Ordered list of key/value tuples (may contain repeated keys).
        strategy: Whether to keep the first or last occurrence of each key.

    Returns:
        DeduplicateResult with the cleaned env and metadata about removed entries.
    """
    from collections import defaultdict

    grouped: Dict[str, List[str]] = defaultdict(list)
    order: List[str] = []

    for key, value in pairs:
        if key not in grouped:
            order.append(key)
        grouped[key].append(value)

    entries: List[DeduplicateEntry] = []
    clean_env: Dict[str, str] = {}

    for key in order:
        values = grouped[key]
        if len(values) == 1:
            clean_env[key] = values[0]
            continue

        if strategy == KeepStrategy.FIRST:
            kept = values[0]
            dropped = values[1:]
        else:
            kept = values[-1]
            dropped = values[:-1]

        clean_env[key] = kept
        entries.append(
            DeduplicateEntry(
                key=key,
                kept_value=kept,
                dropped_values=dropped,
                occurrences=len(values),
            )
        )

    return DeduplicateResult(entries=entries, clean_env=clean_env)
