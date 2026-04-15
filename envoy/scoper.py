"""Scope filtering: restrict an env dict to keys matching a given prefix or set of prefixes."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ScopeEntry:
    key: str
    value: str
    scope: Optional[str]  # matched prefix, or None if unscoped

    def to_dict(self) -> dict:
        return {"key": self.key, "value": self.value, "scope": self.scope}


@dataclass
class ScopeResult:
    entries: List[ScopeEntry] = field(default_factory=list)
    excluded_count: int = 0

    @property
    def env(self) -> Dict[str, str]:
        """Return the filtered env as a plain dict."""
        return {e.key: e.value for e in self.entries}

    @property
    def matched_count(self) -> int:
        return len(self.entries)

    def summary(self) -> str:
        return (
            f"{self.matched_count} key(s) matched, "
            f"{self.excluded_count} excluded."
        )


def scope_env(
    env: Dict[str, str],
    prefixes: List[str],
    *,
    strip_prefix: bool = False,
    case_sensitive: bool = True,
) -> ScopeResult:
    """Filter *env* to only keys whose names start with one of *prefixes*.

    Args:
        env: Source environment mapping.
        prefixes: List of prefix strings to match against.
        strip_prefix: When True, the matched prefix is removed from the key name.
        case_sensitive: When False, prefix comparison is case-insensitive.

    Returns:
        A :class:`ScopeResult` containing matched entries and excluded count.
    """
    if not prefixes:
        entries = [ScopeEntry(key=k, value=v, scope=None) for k, v in env.items()]
        return ScopeResult(entries=entries, excluded_count=0)

    normalised = [
        (p if case_sensitive else p.upper()) for p in prefixes
    ]

    entries: List[ScopeEntry] = []
    excluded = 0

    for key, value in env.items():
        compare_key = key if case_sensitive else key.upper()
        matched_prefix: Optional[str] = None
        for raw_prefix, norm_prefix in zip(prefixes, normalised):
            if compare_key.startswith(norm_prefix):
                matched_prefix = raw_prefix
                break

        if matched_prefix is None:
            excluded += 1
            continue

        out_key = key[len(matched_prefix):] if strip_prefix else key
        entries.append(ScopeEntry(key=out_key, value=value, scope=matched_prefix))

    return ScopeResult(entries=entries, excluded_count=excluded)
