"""Rewriter: apply find-and-replace transformations to .env values."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class RewriteEntry:
    key: str
    original: str
    rewritten: str
    pattern: str
    replacement: str

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "original": self.original,
            "rewritten": self.rewritten,
            "pattern": self.pattern,
            "replacement": self.replacement,
        }


@dataclass
class RewriteResult:
    entries: List[RewriteEntry] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)

    @property
    def changed(self) -> bool:
        return len(self.entries) > 0

    @property
    def changed_count(self) -> int:
        return len(self.entries)

    def summary(self) -> str:
        if not self.changed:
            return "No values rewritten."
        lines = [f"{e.key}: {e.original!r} -> {e.rewritten!r}" for e in self.entries]
        return "\n".join(lines)


def rewrite_env(
    env: Dict[str, str],
    pattern: str,
    replacement: str,
    keys: Optional[List[str]] = None,
    regex: bool = False,
) -> RewriteResult:
    """Rewrite values in *env* by replacing *pattern* with *replacement*.

    Args:
        env: Source environment mapping.
        pattern: The substring (or regex pattern when *regex* is True) to find.
        replacement: The string to substitute in place of each match.
        keys: Optional list of keys to restrict rewrites to.
        regex: When True, treat *pattern* as a regular expression.

    Returns:
        A :class:`RewriteResult` containing changed entries and the updated env.
    """
    result_env = dict(env)
    entries: List[RewriteEntry] = []

    target_keys = keys if keys is not None else list(env.keys())

    for key in target_keys:
        if key not in env:
            continue
        original = env[key]
        if regex:
            rewritten = re.sub(pattern, replacement, original)
        else:
            rewritten = original.replace(pattern, replacement)
        if rewritten != original:
            entries.append(
                RewriteEntry(
                    key=key,
                    original=original,
                    rewritten=rewritten,
                    pattern=pattern,
                    replacement=replacement,
                )
            )
            result_env[key] = rewritten

    return RewriteResult(entries=entries, env=result_env)
