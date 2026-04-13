"""Sort keys in a .env file alphabetically or by custom group order."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SortResult:
    original: Dict[str, str]
    sorted_env: Dict[str, str]
    order: List[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return list(self.original.keys()) != list(self.sorted_env.keys())

    def summary(self) -> str:
        if not self.changed:
            return "Keys already in sorted order."
        return f"Sorted {len(self.sorted_env)} keys."


def sort_env(
    env: Dict[str, str],
    groups: Optional[List[List[str]]] = None,
    case_sensitive: bool = False,
) -> SortResult:
    """Sort env keys alphabetically, optionally grouping specific keys first.

    Args:
        env: The environment dictionary to sort.
        groups: Optional list of key-groups; keys in earlier groups appear first.
        case_sensitive: Whether to sort with case sensitivity.
    Returns:
        SortResult with the sorted dictionary.
    """
    if groups:
        grouped_keys: List[str] = []
        for group in groups:
            for key in group:
                if key in env and key not in grouped_keys:
                    grouped_keys.append(key)
        remaining = [
            k for k in env
            if k not in grouped_keys
        ]
        key_fn = (lambda k: k) if case_sensitive else (lambda k: k.lower())
        remaining_sorted = sorted(remaining, key=key_fn)
        order = grouped_keys + remaining_sorted
    else:
        key_fn = (lambda k: k) if case_sensitive else (lambda k: k.lower())
        order = sorted(env.keys(), key=key_fn)

    sorted_env = {k: env[k] for k in order if k in env}
    return SortResult(original=dict(env), sorted_env=sorted_env, order=order)
