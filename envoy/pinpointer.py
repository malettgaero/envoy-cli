"""Pinpointer: locate which file(s) define a given key across multiple .env files."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PinpointEntry:
    key: str
    sources: List[str]  # files that define this key
    values: Dict[str, str]  # source -> value

    def to_dict(self) -> dict:
        return {"key": self.key, "sources": self.sources, "values": self.values}

    @property
    def is_unique(self) -> bool:
        """True if the key is defined in exactly one file."""
        return len(self.sources) == 1

    @property
    def is_consistent(self) -> bool:
        """True if all files that define the key agree on the value."""
        return len(set(self.values.values())) <= 1


@dataclass
class PinpointResult:
    entries: List[PinpointEntry] = field(default_factory=list)
    searched_files: List[str] = field(default_factory=list)

    def get(self, key: str) -> Optional[PinpointEntry]:
        for e in self.entries:
            if e.key == key:
                return e
        return None

    @property
    def found_keys(self) -> List[str]:
        return [e.key for e in self.entries]

    def summary(self) -> str:
        lines = [f"Searched {len(self.searched_files)} file(s), found {len(self.entries)} key(s)."]
        for e in self.entries:
            status = "consistent" if e.is_consistent else "INCONSISTENT"
            lines.append(f"  {e.key}: {len(e.sources)} source(s) [{status}]")
            for src, val in e.values.items():
                lines.append(f"    {src}: {val!r}")
        return "\n".join(lines)


def pinpoint_env(
    keys: List[str],
    sources: Dict[str, Dict[str, str]],  # label -> parsed env dict
) -> PinpointResult:
    """Locate each key across the given named env sources."""
    result = PinpointResult(searched_files=list(sources.keys()))
    for key in sorted(set(keys)):
        found_sources: List[str] = []
        found_values: Dict[str, str] = {}
        for label, env in sources.items():
            if key in env:
                found_sources.append(label)
                found_values[label] = env[key]
        if found_sources:
            result.entries.append(
                PinpointEntry(key=key, sources=found_sources, values=found_values)
            )
    return result
