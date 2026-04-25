"""envoy.mapper — Build a key-to-files mapping across multiple .env sources."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class MapEntry:
    key: str
    files: List[str]
    values: Dict[str, str]  # filename -> value

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "files": self.files,
            "values": self.values,
        }

    @property
    def is_consistent(self) -> bool:
        """True when the key has the same value in every file it appears in."""
        return len(set(self.values.values())) <= 1

    @property
    def file_count(self) -> int:
        return len(self.files)


@dataclass
class MapResult:
    entries: List[MapEntry] = field(default_factory=list)
    source_files: List[str] = field(default_factory=list)

    @property
    def all_keys(self) -> List[str]:
        return [e.key for e in self.entries]

    @property
    def inconsistent_keys(self) -> List[str]:
        return [e.key for e in self.entries if not e.is_consistent]

    @property
    def unique_to_one_file(self) -> List[str]:
        return [e.key for e in self.entries if e.file_count == 1]

    def entry_for(self, key: str) -> MapEntry | None:
        for e in self.entries:
            if e.key == key:
                return e
        return None

    def summary(self) -> str:
        lines = [
            f"Sources : {len(self.source_files)}",
            f"Keys    : {len(self.entries)}",
            f"Inconsistent: {len(self.inconsistent_keys)}",
            f"Unique  : {len(self.unique_to_one_file)}",
        ]
        return "\n".join(lines)


def map_envs(sources: Dict[str, Dict[str, str]]) -> MapResult:
    """Build a MapResult from a dict of {filename: env_dict}."""
    key_index: Dict[str, MapEntry] = {}

    for filename, env in sources.items():
        for key, value in env.items():
            if key not in key_index:
                key_index[key] = MapEntry(key=key, files=[], values={})
            entry = key_index[key]
            if filename not in entry.files:
                entry.files.append(filename)
            entry.values[filename] = value

    sorted_entries = sorted(key_index.values(), key=lambda e: e.key.lower())
    return MapResult(
        entries=sorted_entries,
        source_files=list(sources.keys()),
    )
