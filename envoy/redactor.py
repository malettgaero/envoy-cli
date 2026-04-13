"""Redactor: mask or strip sensitive keys from an env mapping."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

_DEFAULT_MASK = "***"

_SENSITIVE_PATTERNS: List[str] = [
    "SECRET",
    "PASSWORD",
    "PASSWD",
    "TOKEN",
    "API_KEY",
    "PRIVATE_KEY",
    "AUTH",
    "CREDENTIAL",
]


@dataclass
class RedactEntry:
    key: str
    original: str
    redacted: str
    was_redacted: bool

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "redacted": self.was_redacted,
            "value": self.redacted,
        }


@dataclass
class RedactResult:
    entries: List[RedactEntry] = field(default_factory=list)

    @property
    def env(self) -> Dict[str, str]:
        return {e.key: e.redacted for e in self.entries}

    @property
    def redacted_keys(self) -> List[str]:
        return [e.key for e in self.entries if e.was_redacted]

    def summary(self) -> str:
        n = len(self.redacted_keys)
        if n == 0:
            return "No keys redacted."
        keys = ", ".join(self.redacted_keys)
        return f"{n} key(s) redacted: {keys}"


def _is_sensitive(key: str, extra_patterns: Optional[List[str]] = None) -> bool:
    upper = key.upper()
    patterns = _SENSITIVE_PATTERNS + (extra_patterns or [])
    return any(p in upper for p in patterns)


def redact_env(
    env: Dict[str, str],
    keys: Optional[List[str]] = None,
    mask: str = _DEFAULT_MASK,
    auto_detect: bool = True,
    extra_patterns: Optional[List[str]] = None,
    strip: bool = False,
) -> RedactResult:
    """Return a RedactResult with sensitive values masked or stripped.

    Args:
        env: source env mapping.
        keys: explicit list of keys to redact (in addition to auto-detected).
        mask: replacement string when strip=False.
        auto_detect: if True, redact keys matching built-in sensitive patterns.
        extra_patterns: additional substrings to treat as sensitive.
        strip: if True, remove the key entirely instead of masking.
    """
    explicit = set(keys or [])
    entries: List[RedactEntry] = []

    for k, v in env.items():
        should_redact = k in explicit or (auto_detect and _is_sensitive(k, extra_patterns))
        if should_redact:
            redacted_val = "" if strip else mask
            entries.append(RedactEntry(key=k, original=v, redacted=redacted_val, was_redacted=True))
        else:
            entries.append(RedactEntry(key=k, original=v, redacted=v, was_redacted=False))

    return RedactResult(entries=entries)
