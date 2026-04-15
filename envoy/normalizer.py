"""Normalize .env file keys and values to a consistent format."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class NormalizeEntry:
    key: str
    original_value: str
    normalized_value: str
    original_key: str

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "original_key": self.original_key,
            "original_value": self.original_value,
            "normalized_value": self.normalized_value,
            "key_changed": self.key != self.original_key,
            "value_changed": self.normalized_value != self.original_value,
        }


@dataclass
class NormalizeResult:
    entries: List[NormalizeEntry] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return any(
            e.key != e.original_key or e.normalized_value != e.original_value
            for e in self.entries
        )

    @property
    def changed_count(self) -> int:
        return sum(
            1 for e in self.entries
            if e.key != e.original_key or e.normalized_value != e.original_value
        )

    @property
    def env(self) -> Dict[str, str]:
        return {e.key: e.normalized_value for e in self.entries}

    def summary(self) -> str:
        if not self.changed:
            return "All keys and values are already normalized."
        return f"{self.changed_count} key(s)/value(s) normalized."


def normalize_env(
    env: Dict[str, str],
    *,
    uppercase_keys: bool = True,
    strip_values: bool = True,
    replace_spaces_in_keys: bool = True,
    space_replacement: str = "_",
) -> NormalizeResult:
    """Normalize keys and values in an env dict.

    Args:
        env: Mapping of raw key -> value.
        uppercase_keys: Convert keys to UPPER_CASE.
        strip_values: Strip leading/trailing whitespace from values.
        replace_spaces_in_keys: Replace spaces in keys with *space_replacement*.
        space_replacement: Character used when replacing spaces in keys.

    Returns:
        NormalizeResult containing per-entry details.
    """
    entries: List[NormalizeEntry] = []
    for original_key, original_value in env.items():
        key = original_key
        if replace_spaces_in_keys:
            key = key.replace(" ", space_replacement)
        if uppercase_keys:
            key = key.upper()

        value = original_value
        if strip_values:
            value = value.strip()

        entries.append(
            NormalizeEntry(
                key=key,
                original_key=original_key,
                original_value=original_value,
                normalized_value=value,
            )
        )
    return NormalizeResult(entries=entries)
