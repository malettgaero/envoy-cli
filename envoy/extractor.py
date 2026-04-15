"""Extract a subset of keys from an env dict into a new env dict."""
from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import Dict, List, Optional


@dataclass
class ExtractEntry:
    key: str
    value: str
    matched_by: str  # the pattern or key name that caused inclusion

    def to_dict(self) -> dict:
        return {"key": self.key, "value": self.value, "matched_by": self.matched_by}


@dataclass
class ExtractResult:
    entries: List[ExtractEntry] = field(default_factory=list)
    excluded_keys: List[str] = field(default_factory=list)

    @property
    def env(self) -> Dict[str, str]:
        return {e.key: e.value for e in self.entries}

    @property
    def extracted_count(self) -> int:
        return len(self.entries)

    @property
    def excluded_count(self) -> int:
        return len(self.excluded_keys)

    def summary(self) -> str:
        return (
            f"Extracted {self.extracted_count} key(s), "
            f"excluded {self.excluded_count} key(s)."
        )


def extract_env(
    env: Dict[str, str],
    keys: Optional[List[str]] = None,
    patterns: Optional[List[str]] = None,
) -> ExtractResult:
    """Return a new env containing only keys matched by *keys* or *patterns*.

    If both *keys* and *patterns* are empty/None every key is extracted.
    Glob-style wildcards (``*``, ``?``) are supported in *patterns*.
    """
    if not keys and not patterns:
        entries = [
            ExtractEntry(key=k, value=v, matched_by="*") for k, v in env.items()
        ]
        return ExtractResult(entries=entries, excluded_keys=[])

    explicit: set[str] = set(keys or [])
    pat_list: List[str] = list(patterns or [])

    entries: List[ExtractEntry] = []
    excluded: List[str] = []

    for k, v in env.items():
        if k in explicit:
            entries.append(ExtractEntry(key=k, value=v, matched_by=k))
            continue
        matched_pattern: Optional[str] = next(
            (p for p in pat_list if fnmatch(k, p)), None
        )
        if matched_pattern is not None:
            entries.append(ExtractEntry(key=k, value=v, matched_by=matched_pattern))
        else:
            excluded.append(k)

    return ExtractResult(entries=entries, excluded_keys=sorted(excluded))
