"""Detect and report duplicate keys within a .env file."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class DuplicateEntry:
    key: str
    occurrences: int
    lines: List[int]  # 1-based line numbers where the key appears

    def to_dict(self) -> dict:
        return {"key": self.key, "occurrences": self.occurrences, "lines": self.lines}


@dataclass
class DuplicateResult:
    duplicates: List[DuplicateEntry] = field(default_factory=list)

    @property
    def has_duplicates(self) -> bool:
        return bool(self.duplicates)

    @property
    def summary(self) -> str:
        if not self.has_duplicates:
            return "No duplicate keys found."
        lines = [f"{e.key} (x{e.occurrences}, lines {e.lines})" for e in self.duplicates]
        return "Duplicate keys: " + ", ".join(lines)


def find_duplicates(raw_lines: List[str]) -> DuplicateResult:
    """Scan *raw_lines* (strings from a .env file) and return a DuplicateResult.

    Lines that are blank or start with '#' are ignored.
    """
    seen: Dict[str, List[int]] = {}

    for lineno, raw in enumerate(raw_lines, start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key = stripped.split("=", 1)[0].strip()
        seen.setdefault(key, []).append(lineno)

    entries = [
        DuplicateEntry(key=k, occurrences=len(v), lines=v)
        for k, v in seen.items()
        if len(v) > 1
    ]
    entries.sort(key=lambda e: e.lines[0])
    return DuplicateResult(duplicates=entries)
