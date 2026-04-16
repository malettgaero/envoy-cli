from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class LabelEntry:
    key: str
    value: str
    labels: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"key": self.key, "value": self.value, "labels": self.labels}


@dataclass
class LabelResult:
    entries: List[LabelEntry] = field(default_factory=list)

    def keys_for_label(self, label: str) -> List[str]:
        return [e.key for e in self.entries if label in e.labels]

    def labels_for_key(self, key: str) -> List[str]:
        for e in self.entries:
            if e.key == key:
                return e.labels
        return []

    def all_labels(self) -> List[str]:
        seen: set = set()
        result = []
        for e in self.entries:
            for lbl in e.labels:
                if lbl not in seen:
                    seen.add(lbl)
                    result.append(lbl)
        return sorted(result)

    def env(self) -> Dict[str, str]:
        return {e.key: e.value for e in self.entries}


def label_env(
    env: Dict[str, str],
    label_map: Optional[Dict[str, List[str]]] = None,
) -> LabelResult:
    """
    Assign labels to env keys.

    label_map maps label -> list of key globs/exact keys.
    If label_map is None, keys are returned with no labels.
    """
    import fnmatch

    label_map = label_map or {}

    # Build reverse: key -> labels
    key_labels: Dict[str, List[str]] = {k: [] for k in env}

    for label, patterns in label_map.items():
        for key in env:
            for pattern in patterns:
                if fnmatch.fnmatch(key, pattern):
                    if label not in key_labels[key]:
                        key_labels[key].append(label)
                    break

    entries = [
        LabelEntry(key=k, value=env[k], labels=sorted(key_labels[k]))
        for k in sorted(env)
    ]
    return LabelResult(entries=entries)
