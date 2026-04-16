"""Split a .env file into multiple files based on key prefixes or patterns."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re


@dataclass
class SplitEntry:
    key: str
    value: str
    source_file: str
    target_file: str

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "source_file": self.source_file,
            "target_file": self.target_file,
        }


@dataclass
class SplitResult:
    entries: List[SplitEntry] = field(default_factory=list)
    unmatched: List[str] = field(default_factory=list)

    @property
    def files(self) -> Dict[str, Dict[str, str]]:
        """Return a mapping of target_file -> {key: value}."""
        result: Dict[str, Dict[str, str]] = {}
        for entry in self.entries:
            result.setdefault(entry.target_file, {})[entry.key] = entry.value
        return result

    @property
    def split_count(self) -> int:
        return len(self.files)

    def summary(self) -> str:
        parts = [f"Split into {self.split_count} file(s), {len(self.entries)} key(s) assigned"]
        if self.unmatched:
            parts.append(f"{len(self.unmatched)} key(s) unmatched")
        return "; ".join(parts)


def split_env(
    env: Dict[str, str],
    prefix_map: Dict[str, str],
    source_file: str = "<env>",
    default_file: Optional[str] = None,
    strip_prefix: bool = False,
) -> SplitResult:
    """Split *env* keys into target files according to *prefix_map*.

    Args:
        env: The environment dict to split.
        prefix_map: Mapping of prefix (or regex pattern) -> target filename.
        source_file: Label for the source used in entries.
        default_file: If set, unmatched keys go here; otherwise they land in
            ``unmatched``.
        strip_prefix: When True, remove the matched prefix from the key name
            in the output.
    """
    entries: List[SplitEntry] = []
    unmatched: List[str] = []

    for key, value in env.items():
        matched_target: Optional[str] = None
        matched_prefix: Optional[str] = None

        for pattern, target in prefix_map.items():
            if re.match(pattern, key, re.IGNORECASE):
                matched_target = target
                matched_prefix = pattern
                break

        if matched_target is None:
            if default_file is not None:
                entries.append(SplitEntry(key, value, source_file, default_file))
            else:
                unmatched.append(key)
            continue

        out_key = key
        if strip_prefix and matched_prefix:
            # Strip a simple literal prefix (non-regex) from the key
            literal = matched_prefix.rstrip(".*+?$").lstrip("^")
            if key.upper().startswith(literal.upper()):
                out_key = key[len(literal):].lstrip("_")

        entries.append(SplitEntry(out_key, value, source_file, matched_target))

    return SplitResult(entries=entries, unmatched=unmatched)
