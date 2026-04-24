"""Inject environment variables into a running process environment or shell export block."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class InjectEntry:
    key: str
    value: str
    overwritten: bool = False
    source: str = ""

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "overwritten": self.overwritten,
            "source": self.source,
        }


@dataclass
class InjectResult:
    entries: List[InjectEntry] = field(default_factory=list)
    base_env: Dict[str, str] = field(default_factory=dict)

    @property
    def env(self) -> Dict[str, str]:
        """Return the merged environment after injection."""
        merged = dict(self.base_env)
        for e in self.entries:
            merged[e.key] = e.value
        return merged

    @property
    def injected_count(self) -> int:
        return len(self.entries)

    @property
    def overwritten_count(self) -> int:
        return sum(1 for e in self.entries if e.overwritten)

    def summary(self) -> str:
        return (
            f"{self.injected_count} key(s) injected, "
            f"{self.overwritten_count} overwritten."
        )


def inject_env(
    base: Dict[str, str],
    source: Dict[str, str],
    keys: Optional[List[str]] = None,
    overwrite: bool = True,
    source_label: str = "",
) -> InjectResult:
    """Inject keys from *source* into *base*.

    Args:
        base: The target environment mapping.
        source: The source environment mapping to inject from.
        keys: Optional list of specific keys to inject. Injects all if None.
        overwrite: If False, existing keys in *base* are skipped.
        source_label: Human-readable label for the source (e.g. filename).

    Returns:
        InjectResult with details of what was injected.
    """
    result = InjectResult(base_env=dict(base))
    candidates = keys if keys is not None else list(source.keys())

    for key in candidates:
        if key not in source:
            continue
        value = source[key]
        already_present = key in base
        if already_present and not overwrite:
            continue
        result.entries.append(
            InjectEntry(
                key=key,
                value=value,
                overwritten=already_present,
                source=source_label,
            )
        )

    return result
