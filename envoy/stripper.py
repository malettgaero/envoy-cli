"""Strip comments and blank lines from .env files, returning a clean version."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class StripEntry:
    line_number: int
    original: str
    reason: str  # 'comment' | 'blank'

    def to_dict(self) -> dict:
        return {
            "line_number": self.line_number,
            "original": self.original,
            "reason": self.reason,
        }


@dataclass
class StripResult:
    entries: List[StripEntry] = field(default_factory=list)
    cleaned_lines: List[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return len(self.entries) > 0

    @property
    def removed_count(self) -> int:
        return len(self.entries)

    def summary(self) -> str:
        if not self.changed:
            return "No comments or blank lines found."
        comments = sum(1 for e in self.entries if e.reason == "comment")
        blanks = sum(1 for e in self.entries if e.reason == "blank")
        parts = []
        if comments:
            parts.append(f"{comments} comment(s)")
        if blanks:
            parts.append(f"{blanks} blank line(s)")
        return f"Removed {' and '.join(parts)}."


def strip_env(lines: List[str]) -> StripResult:
    """Remove comment lines and blank lines from raw .env file lines.

    Args:
        lines: Raw lines from an .env file (may include newline characters).

    Returns:
        StripResult with removed entries and the cleaned line list.
    """
    result = StripResult()

    for i, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if stripped == "":
            result.entries.append(StripEntry(line_number=i, original=raw.rstrip("\n"), reason="blank"))
        elif stripped.startswith("#"):
            result.entries.append(StripEntry(line_number=i, original=raw.rstrip("\n"), reason="comment"))
        else:
            result.cleaned_lines.append(raw if raw.endswith("\n") else raw + "\n")

    return result
