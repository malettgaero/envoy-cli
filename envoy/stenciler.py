"""stenciler.py – apply a key-whitelist stencil to an env mapping.

A *stencil* is an ordered list of key names that defines the exact set of
keys (and their display order) that should appear in an output env.  Keys
present in the source but absent from the stencil are dropped; keys listed
in the stencil but absent from the source are recorded as missing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class StencilEntry:
    key: str
    value: Optional[str]   # None  → key was listed in stencil but not in source
    in_source: bool
    in_stencil: bool

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "in_source": self.in_source,
            "in_stencil": self.in_stencil,
        }


@dataclass
class StencilResult:
    entries: List[StencilEntry] = field(default_factory=list)
    _source: Dict[str, str] = field(default_factory=dict, repr=False)

    # ------------------------------------------------------------------ #
    # convenience properties
    # ------------------------------------------------------------------ #

    @property
    def env(self) -> Dict[str, str]:
        """Only the keys that were both in the stencil *and* the source."""
        return {
            e.key: e.value  # type: ignore[return-value]
            for e in self.entries
            if e.in_source and e.in_stencil
        }

    @property
    def missing_keys(self) -> List[str]:
        """Keys listed in the stencil that were absent from the source."""
        return [e.key for e in self.entries if not e.in_source]

    @property
    def dropped_keys(self) -> List[str]:
        """Source keys that were not in the stencil (and therefore dropped)."""
        stencil_set = {e.key for e in self.entries}
        return [k for k in self._source if k not in stencil_set]

    @property
    def passed(self) -> bool:
        return len(self.missing_keys) == 0

    def summary(self) -> str:
        kept = len(self.env)
        missing = len(self.missing_keys)
        dropped = len(self.dropped_keys)
        return (
            f"{kept} key(s) kept, {missing} missing from source, "
            f"{dropped} dropped (not in stencil)"
        )


def apply_stencil(
    source: Dict[str, str],
    stencil: List[str],
) -> StencilResult:
    """Apply *stencil* (ordered key list) to *source* env dict."""
    entries: List[StencilEntry] = []

    for key in stencil:
        if key in source:
            entries.append(StencilEntry(key=key, value=source[key], in_source=True, in_stencil=True))
        else:
            entries.append(StencilEntry(key=key, value=None, in_source=False, in_stencil=True))

    result = StencilResult(entries=entries)
    result._source = dict(source)
    return result
