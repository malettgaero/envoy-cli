"""Tag env keys with arbitrary labels for grouping and filtering."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass
class TagEntry:
    key: str
    tags: Set[str]

    def to_dict(self) -> dict:
        return {"key": self.key, "tags": sorted(self.tags)}


@dataclass
class TagResult:
    entries: List[TagEntry] = field(default_factory=list)
    _index: Dict[str, TagEntry] = field(default_factory=dict, repr=False)

    def keys_for_tag(self, tag: str) -> List[str]:
        """Return all keys that carry *tag*."""
        return [e.key for e in self.entries if tag in e.tags]

    def tags_for_key(self, key: str) -> Set[str]:
        """Return the tag-set for *key*, or an empty set."""
        entry = self._index.get(key)
        return set(entry.tags) if entry else set()

    def all_tags(self) -> Set[str]:
        """Return every distinct tag present in the result."""
        out: Set[str] = set()
        for e in self.entries:
            out |= e.tags
        return out

    def summary(self) -> str:
        total = len(self.entries)
        tagged = sum(1 for e in self.entries if e.tags)
        return f"{tagged}/{total} keys tagged across {len(self.all_tags())} distinct tag(s)"


def tag_env(
    env: Dict[str, str],
    tag_map: Dict[str, List[str]],
) -> TagResult:
    """Apply *tag_map* (key -> list[tag]) to *env*.

    Keys present in *env* but absent from *tag_map* receive an empty tag-set.
    Keys in *tag_map* that are not in *env* are silently ignored.
    """
    entries: List[TagEntry] = []
    index: Dict[str, TagEntry] = {}

    for key in sorted(env):
        tags: Set[str] = set(tag_map.get(key, []))
        entry = TagEntry(key=key, tags=tags)
        entries.append(entry)
        index[key] = entry

    result = TagResult(entries=entries, _index=index)
    return result
