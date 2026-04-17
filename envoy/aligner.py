"""Align .env file values by padding keys to a consistent column width."""
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class AlignEntry:
    key: str
    original_line: str
    aligned_line: str

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "original_line": self.original_line,
            "aligned_line": self.aligned_line,
        }


@dataclass
class AlignResult:
    entries: List[AlignEntry] = field(default_factory=list)
    lines_out: List[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return any(e.original_line != e.aligned_line for e in self.entries)

    @property
    def changed_count(self) -> int:
        return sum(1 for e in self.entries if e.original_line != e.aligned_line)

    def summary(self) -> str:
        if not self.changed:
            return "Already aligned — no changes needed."
        return f"{self.changed_count} line(s) realigned."


def align_env(lines: List[str], separator: str = " = ") -> AlignResult:
    """Align KEY=VALUE lines so the '=' signs line up at a common column."""
    pairs: List[Tuple[int, str, str]] = []
    for idx, line in enumerate(lines):
        stripped = line.rstrip("\n")
        if stripped.startswith("#") or "=" not in stripped or stripped.strip() == "":
            continue
        key, _, value = stripped.partition("=")
        if key.strip():
            pairs.append((idx, key.rstrip(), value.lstrip()))

    if not pairs:
        return AlignResult(entries=[], lines_out=list(lines))

    max_key_len = max(len(k) for _, k, _ in pairs)

    entries: List[AlignEntry] = []
    lines_out = list(lines)
    for idx, key, value in pairs:
        original = lines[idx].rstrip("\n")
        padded_key = key.ljust(max_key_len)
        aligned = f"{padded_key}{separator}{value}"
        lines_out[idx] = aligned + "\n" if lines[idx].endswith("\n") else aligned
        entries.append(AlignEntry(key=key.strip(), original_line=original, aligned_line=aligned))

    return AlignResult(entries=entries, lines_out=lines_out)
