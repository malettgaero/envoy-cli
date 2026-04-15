"""sanitizer.py – strip or replace unsafe characters from .env values."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re

_CONTROL_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
_NEWLINE_RE = re.compile(r"[\r\n]")


@dataclass
class SanitizeEntry:
    key: str
    original: str
    sanitized: str
    issues: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "original": self.original,
            "sanitized": self.sanitized,
            "issues": self.issues,
        }


@dataclass
class SanitizeResult:
    entries: List[SanitizeEntry] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return any(e.original != e.sanitized for e in self.entries)

    @property
    def changed_count(self) -> int:
        return sum(1 for e in self.entries if e.original != e.sanitized)

    @property
    def env(self) -> Dict[str, str]:
        return {e.key: e.sanitized for e in self.entries}

    def summary(self) -> str:
        if not self.changed:
            return "No sanitization needed."
        lines = [f"{self.changed_count} key(s) sanitized:"]
        for e in self.entries:
            if e.original != e.sanitized:
                lines.append(f"  {e.key}: {', '.join(e.issues)}")
        return "\n".join(lines)


def sanitize_env(
    env: Dict[str, str],
    *,
    strip_newlines: bool = True,
    strip_control_chars: bool = True,
    strip_leading_trailing_whitespace: bool = True,
    replacement: str = "",
) -> SanitizeResult:
    """Return a SanitizeResult with cleaned values for every key in *env*."""
    entries: List[SanitizeEntry] = []

    for key, value in env.items():
        sanitized = value
        issues: List[str] = []

        if strip_leading_trailing_whitespace and sanitized != sanitized.strip():
            sanitized = sanitized.strip()
            issues.append("leading/trailing whitespace removed")

        if strip_newlines and _NEWLINE_RE.search(sanitized):
            sanitized = _NEWLINE_RE.sub(replacement, sanitized)
            issues.append("embedded newlines removed")

        if strip_control_chars and _CONTROL_RE.search(sanitized):
            sanitized = _CONTROL_RE.sub(replacement, sanitized)
            issues.append("control characters removed")

        entries.append(SanitizeEntry(key=key, original=value, sanitized=sanitized, issues=issues))

    return SanitizeResult(entries=entries)
