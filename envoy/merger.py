"""Merge multiple .env files with conflict detection and override strategies."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class Strategy(str, Enum):
    FIRST_WINS = "first_wins"
    LAST_WINS = "last_wins"
    STRICT = "strict"  # raise on conflict


@dataclass
class MergeConflict:
    key: str
    values: List[Tuple[str, str]]  # list of (source_label, value)

    def __str__(self) -> str:
        sources = ", ".join(f"{label}={val!r}" for label, val in self.values)
        return f"Conflict on '{self.key}': {sources}"


@dataclass
class MergeResult:
    merged: Dict[str, str] = field(default_factory=dict)
    conflicts: List[MergeConflict] = field(default_factory=list)
    sources_used: List[str] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0

    def summary(self) -> str:
        lines = [f"Merged {len(self.sources_used)} source(s), {len(self.merged)} key(s) total."]
        if self.conflicts:
            lines.append(f"  {len(self.conflicts)} conflict(s) detected:")
            for c in self.conflicts:
                lines.append(f"    - {c}")
        return "\n".join(lines)


class MergeError(Exception):
    pass


def merge_envs(
    envs: List[Tuple[str, Dict[str, str]]],
    strategy: Strategy = Strategy.LAST_WINS,
) -> MergeResult:
    """Merge a list of (label, env_dict) pairs into a single MergeResult."""
    if not envs:
        return MergeResult()

    result = MergeResult(sources_used=[label for label, _ in envs])
    conflict_map: Dict[str, List[Tuple[str, str]]] = {}

    for label, env in envs:
        for key, value in env.items():
            if key in result.merged and result.merged[key] != value:
                conflict_map.setdefault(key, [])
                if not conflict_map[key]:
                    # record the original value and its source
                    prev_label = _find_source(key, envs, label)
                    conflict_map[key].append((prev_label, result.merged[key]))
                conflict_map[key].append((label, value))

                if strategy == Strategy.STRICT:
                    raise MergeError(f"Conflict on key '{key}' between sources.")
                elif strategy == Strategy.LAST_WINS:
                    result.merged[key] = value
                # FIRST_WINS: keep existing value, do nothing
            else:
                result.merged[key] = value

    result.conflicts = [
        MergeConflict(key=k, values=v) for k, v in conflict_map.items()
    ]
    return result


def _find_source(
    key: str,
    envs: List[Tuple[str, Dict[str, str]]],
    current_label: str,
) -> str:
    """Return the label of the first source that defined the key before current_label."""
    for label, env in envs:
        if label == current_label:
            break
        if key in env:
            return label
    return "unknown"
