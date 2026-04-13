"""Multi-environment comparison: compare N .env files side-by-side."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class CompareEntry:
    """Value of a single key across all compared environments."""
    key: str
    values: Dict[str, Optional[str]]  # env_name -> value (None = missing)

    @property
    def is_consistent(self) -> bool:
        """True when all environments share the same non-None value."""
        present = [v for v in self.values.values() if v is not None]
        return len(present) == len(self.values) and len(set(present)) == 1

    @property
    def is_missing_in_some(self) -> bool:
        return any(v is None for v in self.values.values())


@dataclass
class CompareResult:
    entries: List[CompareEntry] = field(default_factory=list)
    env_names: List[str] = field(default_factory=list)

    @property
    def all_keys(self) -> List[str]:
        return [e.key for e in self.entries]

    @property
    def inconsistent_entries(self) -> List[CompareEntry]:
        return [e for e in self.entries if not e.is_consistent]

    @property
    def missing_entries(self) -> List[CompareEntry]:
        return [e for e in self.entries if e.is_missing_in_some]

    def summary(self) -> str:
        lines = [
            f"Environments compared : {', '.join(self.env_names)}",
            f"Total keys            : {len(self.entries)}",
            f"Inconsistent values   : {len(self.inconsistent_entries)}",
            f"Keys missing somewhere: {len(self.missing_entries)}",
        ]
        return "\n".join(lines)


def compare_envs(
    envs: Dict[str, Dict[str, str]],
    mask_secrets: bool = False,
) -> CompareResult:
    """Compare multiple environments keyed by name.

    Args:
        envs: mapping of environment-name -> parsed key/value dict.
        mask_secrets: if True, replace values with ``***`` in the result.

    Returns:
        A :class:`CompareResult` with one entry per unique key.
    """
    all_keys: Set[str] = set()
    for env in envs.values():
        all_keys.update(env.keys())

    env_names = list(envs.keys())
    entries: List[CompareEntry] = []

    for key in sorted(all_keys):
        values: Dict[str, Optional[str]] = {}
        for name, env in envs.items():
            raw = env.get(key)  # None when key absent
            if raw is not None and mask_secrets:
                raw = "***"
            values[name] = raw
        entries.append(CompareEntry(key=key, values=values))

    return CompareResult(entries=entries, env_names=env_names)
