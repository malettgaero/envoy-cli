"""Flatten nested key structures into a single-level .env dict.

Supports dot-notation keys (e.g. DB.HOST -> DB__HOST) and provides
a reverse unflatten operation for round-trip support.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FlattenEntry:
    original_key: str
    flat_key: str
    value: str

    def to_dict(self) -> dict:
        return {
            "original_key": self.original_key,
            "flat_key": self.flat_key,
            "value": self.value,
        }


@dataclass
class FlattenResult:
    entries: List[FlattenEntry] = field(default_factory=list)
    separator: str = "__"

    @property
    def env(self) -> Dict[str, str]:
        """Return the flattened key->value mapping."""
        return {e.flat_key: e.value for e in self.entries}

    @property
    def changed(self) -> List[FlattenEntry]:
        """Entries whose key was actually transformed."""
        return [e for e in self.entries if e.original_key != e.flat_key]

    @property
    def changed_count(self) -> int:
        return len(self.changed)

    def summary(self) -> str:
        total = len(self.entries)
        changed = self.changed_count
        if changed == 0:
            return f"All {total} key(s) already flat — no changes."
        return f"{changed}/{total} key(s) flattened."


def flatten_env(
    env: Dict[str, str],
    separator: str = "__",
    source_sep: str = ".",
) -> FlattenResult:
    """Flatten dot-notation keys to separator-notation.

    Args:
        env: Input key-value mapping.
        separator: Replacement separator written into flat keys (default ``__``).
        source_sep: The separator present in the *input* keys (default ``.``).

    Returns:
        A :class:`FlattenResult` describing every key transformation.
    """
    entries: List[FlattenEntry] = []
    for key, value in env.items():
        flat_key = key.replace(source_sep, separator) if source_sep in key else key
        entries.append(FlattenEntry(original_key=key, flat_key=flat_key, value=value))
    return FlattenResult(entries=entries, separator=separator)


def unflatten_env(
    env: Dict[str, str],
    separator: str = "__",
    target_sep: str = ".",
) -> Dict[str, str]:
    """Reverse a previously flattened env back to dot-notation keys."""
    return {
        k.replace(separator, target_sep) if separator in k else k: v
        for k, v in env.items()
    }
