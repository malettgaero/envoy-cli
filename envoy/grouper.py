"""Group env keys by prefix (e.g. DB_, AWS_, APP_) for organised display."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class GroupEntry:
    key: str
    value: str
    prefix: str  # empty string means "ungrouped"

    def to_dict(self) -> dict:
        return {"key": self.key, "value": self.value, "prefix": self.prefix}


@dataclass
class GroupResult:
    entries: List[GroupEntry] = field(default_factory=list)

    # --- derived helpers ---------------------------------------------------

    @property
    def groups(self) -> Dict[str, List[GroupEntry]]:
        """Return a mapping of prefix -> sorted list of entries."""
        result: Dict[str, List[GroupEntry]] = {}
        for e in self.entries:
            result.setdefault(e.prefix, []).append(e)
        return dict(sorted(result.items()))

    def keys_for_prefix(self, prefix: str) -> List[str]:
        return [e.key for e in self.entries if e.prefix == prefix]

    def prefix_for_key(self, key: str) -> Optional[str]:
        for e in self.entries:
            if e.key == key:
                return e.prefix
        return None

    def summary(self) -> str:
        g = self.groups
        parts = []
        for prefix, items in g.items():
            label = prefix if prefix else "(ungrouped)"
            parts.append(f"{label}: {len(items)} key(s)")
        return ", ".join(parts) if parts else "no keys"


def _detect_prefix(key: str, delimiters: str = "_") -> str:
    """Return the first segment before a delimiter, uppercased, or '' if none."""
    for delim in delimiters:
        if delim in key:
            return key.split(delim)[0].upper()
    return ""


def group_env(
    env: Dict[str, str],
    prefixes: Optional[List[str]] = None,
    *,
    auto_detect: bool = True,
) -> GroupResult:
    """Group *env* keys by prefix.

    Parameters
    ----------
    env:         Parsed env mapping.
    prefixes:    Explicit list of prefixes to match (case-insensitive).
                 Keys not matching any prefix land in the '' (ungrouped) bucket.
    auto_detect: When *prefixes* is None, automatically detect prefixes from
                 the keys themselves using underscore as delimiter.
    """
    entries: List[GroupEntry] = []

    explicit = [p.upper() for p in prefixes] if prefixes is not None else None

    for key in sorted(env):
        value = env[key]
        if explicit is not None:
            matched = next((p for p in explicit if key.upper().startswith(p + "_")), "")
            prefix = matched
        elif auto_detect:
            prefix = _detect_prefix(key)
        else:
            prefix = ""
        entries.append(GroupEntry(key=key, value=value, prefix=prefix))

    return GroupResult(entries=entries)
