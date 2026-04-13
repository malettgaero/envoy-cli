"""Resolve environment variable values from multiple sources with priority ordering."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class ResolvedEntry:
    key: str
    value: str
    source: str  # label/name of the source file or dict that provided the value
    overridden_by: Optional[str] = None  # source that took priority over this one

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "source": self.source,
            "overridden_by": self.overridden_by,
        }


@dataclass
class ResolveResult:
    resolved: Dict[str, ResolvedEntry] = field(default_factory=dict)
    shadowed: List[ResolvedEntry] = field(default_factory=list)

    @property
    def env(self) -> Dict[str, str]:
        """Return the final flat key/value mapping."""
        return {k: e.value for k, e in self.resolved.items()}

    def summary(self) -> str:
        lines = [f"Resolved {len(self.resolved)} key(s)."]
        if self.shadowed:
            lines.append(f"{len(self.shadowed)} key(s) were shadowed by higher-priority sources:")
            for entry in self.shadowed:
                lines.append(f"  {entry.key}: '{entry.value}' from '{entry.source}' overridden by '{entry.overridden_by}'")
        return "\n".join(lines)


def resolve_envs(
    sources: List[Tuple[str, Dict[str, str]]],
    *,
    last_wins: bool = True,
) -> ResolveResult:
    """Resolve variables from multiple sources.

    Args:
        sources: Ordered list of (label, env_dict) pairs. Earlier sources have
                 lower priority when last_wins=True (default), higher otherwise.
        last_wins: If True, later sources override earlier ones (default).
                   If False, the first source that defines a key wins.

    Returns:
        A ResolveResult with the final resolved values and shadowed entries.
    """
    if not last_wins:
        sources = list(reversed(sources))

    resolved: Dict[str, ResolvedEntry] = {}
    shadowed: List[ResolvedEntry] = []

    for label, env in sources:
        for key, value in env.items():
            if key in resolved:
                existing = resolved[key]
                shadowed.append(
                    ResolvedEntry(
                        key=existing.key,
                        value=existing.value,
                        source=existing.source,
                        overridden_by=label,
                    )
                )
            resolved[key] = ResolvedEntry(key=key, value=value, source=label)

    return ResolveResult(resolved=resolved, shadowed=shadowed)
