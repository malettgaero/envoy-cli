"""envoy.linker — detect and resolve cross-file key references.

A *link* is a key whose value in one env file references a key that should
exist in another env file (e.g. DATABASE_URL = ${PROD_DATABASE_URL}).  The
linker scans multiple env dicts, builds a reference graph, and reports which
cross-file references are satisfied, broken, or circular.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

# Matches ${VAR} or $VAR style references inside values
_REF_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


@dataclass
class LinkEntry:
    """Represents a single cross-file reference discovered during linking."""

    source_file: str        # label of the file that contains the referencing key
    source_key: str         # key whose value contains the reference
    ref_key: str            # the variable name being referenced
    resolved_in: Optional[str]  # label of the file where ref_key was found, or None
    value: Optional[str]    # resolved value, or None if broken
    broken: bool            # True when ref_key is not found in any provided file

    def to_dict(self) -> dict:
        return {
            "source_file": self.source_file,
            "source_key": self.source_key,
            "ref_key": self.ref_key,
            "resolved_in": self.resolved_in,
            "value": self.value,
            "broken": self.broken,
        }


@dataclass
class LinkResult:
    """Aggregated result of a cross-file link analysis."""

    entries: List[LinkEntry] = field(default_factory=list)
    # files that were analysed, in the order they were supplied
    files: List[str] = field(default_factory=list)

    # ------------------------------------------------------------------ #
    # Convenience properties
    # ------------------------------------------------------------------ #

    @property
    def broken(self) -> List[LinkEntry]:
        """All entries where the reference could not be resolved."""
        return [e for e in self.entries if e.broken]

    @property
    def resolved(self) -> List[LinkEntry]:
        """All entries where the reference was successfully resolved."""
        return [e for e in self.entries if not e.broken]

    @property
    def has_broken_links(self) -> bool:
        return bool(self.broken)

    def summary(self) -> str:
        total = len(self.entries)
        ok = len(self.resolved)
        bad = len(self.broken)
        if total == 0:
            return "No cross-file references found."
        parts = [f"{total} reference(s) found: {ok} resolved, {bad} broken."]
        for e in self.broken:
            parts.append(
                f"  BROKEN  {e.source_file}::{e.source_key} -> ${e.ref_key}"
            )
        return "\n".join(parts)


def _extract_refs(value: str) -> List[str]:
    """Return all variable names referenced inside *value*."""
    refs: List[str] = []
    for m in _REF_RE.finditer(value):
        refs.append(m.group(1) or m.group(2))
    return refs


def link_envs(
    sources: List[Tuple[str, Dict[str, str]]],
) -> LinkResult:
    """Analyse cross-file references across *sources*.

    Parameters
    ----------
    sources:
        An ordered list of ``(label, env_dict)`` pairs.  The label is used
        only for reporting (e.g. the filename).

    Returns
    -------
    LinkResult
        Contains every cross-file reference discovered, together with
        resolution status.
    """
    if not sources:
        return LinkResult()

    file_labels = [label for label, _ in sources]

    # Build a merged lookup: key -> (label, value) — last definition wins
    # for resolution purposes (mirrors cascade/resolver behaviour).
    global_lookup: Dict[str, Tuple[str, str]] = {}
    for label, env in sources:
        for k, v in env.items():
            global_lookup[k] = (label, v)

    entries: List[LinkEntry] = []

    for label, env in sources:
        for key, value in env.items():
            refs = _extract_refs(value)
            for ref in refs:
                # A cross-file reference is only interesting when the ref_key
                # does NOT live in the same file.
                if ref in env:
                    # self-reference within the same file — skip
                    continue

                if ref in global_lookup:
                    resolved_label, resolved_value = global_lookup[ref]
                    entries.append(
                        LinkEntry(
                            source_file=label,
                            source_key=key,
                            ref_key=ref,
                            resolved_in=resolved_label,
                            value=resolved_value,
                            broken=False,
                        )
                    )
                else:
                    entries.append(
                        LinkEntry(
                            source_file=label,
                            source_key=key,
                            ref_key=ref,
                            resolved_in=None,
                            value=None,
                            broken=True,
                        )
                    )

    # Stable sort: broken first, then by source_file + source_key
    entries.sort(key=lambda e: (not e.broken, e.source_file, e.source_key))

    return LinkResult(entries=entries, files=file_labels)
