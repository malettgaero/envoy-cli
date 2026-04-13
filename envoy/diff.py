"""Secret diffing support: compare two parsed .env dictionaries."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DiffResult:
    """Holds the diff between two .env files."""

    added: Dict[str, str] = field(default_factory=dict)
    removed: Dict[str, str] = field(default_factory=dict)
    changed: Dict[str, tuple] = field(default_factory=dict)  # key -> (old, new)
    unchanged: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        lines = []
        for key, value in sorted(self.added.items()):
            lines.append(f"  + {key}={_mask(value)}")
        for key, value in sorted(self.removed.items()):
            lines.append(f"  - {key}={_mask(value)}")
        for key, (old, new) in sorted(self.changed.items()):
            lines.append(f"  ~ {key}: {_mask(old)} -> {_mask(new)}")
        if not lines:
            lines.append("  (no changes)")
        return "\n".join(lines)


def diff_envs(
    base: Dict[str, str],
    target: Dict[str, str],
    mask_secrets: bool = True,
) -> DiffResult:
    """Compare two env dicts and return a DiffResult.

    Args:
        base:   The reference environment (e.g. .env.example).
        target: The environment being compared (e.g. .env.production).
        mask_secrets: When True, values are masked in the summary output.

    Returns:
        A DiffResult describing additions, removals, and changes.
    """
    result = DiffResult()
    all_keys = set(base) | set(target)

    for key in all_keys:
        in_base = key in base
        in_target = key in target

        if in_base and not in_target:
            result.removed[key] = base[key]
        elif in_target and not in_base:
            result.added[key] = target[key]
        elif base[key] != target[key]:
            result.changed[key] = (base[key], target[key])
        else:
            result.unchanged.append(key)

    return result


def _mask(value: str, visible: int = 4) -> str:
    """Partially mask a secret value for safe display."""
    if len(value) <= visible:
        return "*" * len(value)
    return value[:visible] + "*" * (len(value) - visible)
