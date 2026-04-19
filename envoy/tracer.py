"""Trace where each key in a final env came from across a chain of source files."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TraceEntry:
    key: str
    value: str
    source: str
    overridden_by: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "source": self.source,
            "overridden_by": self.overridden_by,
        }


@dataclass
class TraceResult:
    entries: List[TraceEntry] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)

    @property
    def env(self) -> Dict[str, str]:
        return {e.key: e.value for e in self.entries if e.overridden_by is None}

    @property
    def overridden(self) -> List[TraceEntry]:
        return [e for e in self.entries if e.overridden_by is not None]

    def source_for(self, key: str) -> Optional[str]:
        for e in self.entries:
            if e.key == key and e.overridden_by is None:
                return e.source
        return None

    def summary(self) -> str:
        active = len(self.env)
        shadowed = len(self.overridden)
        return f"{active} active keys, {shadowed} shadowed across {len(self.sources)} sources"


def trace_env(sources: Dict[str, Dict[str, str]]) -> TraceResult:
    """Trace key provenance across ordered sources (later sources override earlier).

    Args:
        sources: OrderedDict-like mapping of label -> env dict.
    """
    source_names = list(sources.keys())
    # key -> (value, source_label)
    active: Dict[str, tuple] = {}
    all_entries: List[TraceEntry] = []

    for label, env in sources.items():
        for key, value in env.items():
            if key in active:
                prev_value, prev_source = active[key]
                # mark previous entry as overridden
                for e in all_entries:
                    if e.key == key and e.source == prev_source and e.overridden_by is None:
                        e.overridden_by = label
                        break
            active[key] = (value, label)
            all_entries.append(TraceEntry(key=key, value=value, source=label))

    return TraceResult(entries=all_entries, sources=source_names)
