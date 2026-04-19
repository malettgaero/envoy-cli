"""Auto-fix common lint issues in .env files."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class FixEntry:
    line_number: int
    original: str
    fixed: str
    reason: str

    def to_dict(self) -> Dict:
        return {
            "line_number": self.line_number,
            "original": self.original,
            "fixed": self.fixed,
            "reason": self.reason,
        }


@dataclass
class FixResult:
    entries: List[FixEntry] = field(default_factory=list)
    lines: List[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return len(self.entries) > 0

    @property
    def changed_count(self) -> int:
        return len(self.entries)

    def summary(self) -> str:
        if not self.changed:
            return "No fixes applied."
        return f"{self.changed_count} fix(es) applied."


def fix_env(lines: List[str]) -> FixResult:
    """Apply automatic fixes to raw .env file lines."""
    result = FixResult()
    fixed_lines: List[str] = []

    for i, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")
        stripped = line.strip()

        # Skip blanks and comments
        if not stripped or stripped.startswith("#"):
            fixed_lines.append(line)
            continue

        if "=" not in stripped:
            fixed_lines.append(line)
            continue

        key, _, value = stripped.partition("=")
        original_key = key
        original_value = value

        # Fix 1: uppercase key
        fixed_key = key.strip().upper()

        # Fix 2: strip whitespace around value
        fixed_value = value.strip()

        fixed_line = f"{fixed_key}={fixed_value}"

        if fixed_line != stripped:
            result.entries.append(
                FixEntry(
                    line_number=i,
                    original=stripped,
                    fixed=fixed_line,
                    reason=_describe_fix(original_key, fixed_key, original_value, fixed_value),
                )
            )
            fixed_lines.append(fixed_line)
        else:
            fixed_lines.append(line)

    result.lines = fixed_lines
    return result


def _describe_fix(orig_key: str, fixed_key: str, orig_val: str, fixed_val: str) -> str:
    reasons = []
    if orig_key.strip() != fixed_key:
        reasons.append("key uppercased")
    if orig_val != fixed_val:
        reasons.append("value whitespace stripped")
    return ", ".join(reasons) if reasons else "reformatted"
