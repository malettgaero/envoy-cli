"""envoy.masker — Mask sensitive values in an env dict for safe display."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

_SENSITIVE_PATTERNS: List[str] = [
    "password", "passwd", "secret", "token", "api_key", "apikey",
    "auth", "credential", "private", "access_key", "signing",
]

DEFAULT_MASK = "********"


@dataclass
class MaskEntry:
    key: str
    original: str
    masked: str
    was_masked: bool

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "masked": self.masked,
            "was_masked": self.was_masked,
        }


@dataclass
class MaskResult:
    entries: List[MaskEntry] = field(default_factory=list)

    @property
    def env(self) -> Dict[str, str]:
        """Return the env dict with sensitive values replaced."""
        return {e.key: e.masked for e in self.entries}

    @property
    def masked_keys(self) -> List[str]:
        return [e.key for e in self.entries if e.was_masked]

    @property
    def masked_count(self) -> int:
        return len(self.masked_keys)

    def summary(self) -> str:
        if self.masked_count == 0:
            return "No sensitive keys detected."
        keys = ", ".join(self.masked_keys)
        return f"{self.masked_count} key(s) masked: {keys}"


def _is_sensitive(key: str, sensitive_keys: Optional[Set[str]]) -> bool:
    lower = key.lower()
    if sensitive_keys is not None:
        return key in sensitive_keys or lower in {s.lower() for s in sensitive_keys}
    return any(pat in lower for pat in _SENSITIVE_PATTERNS)


def mask_env(
    env: Dict[str, str],
    *,
    sensitive_keys: Optional[Set[str]] = None,
    mask: str = DEFAULT_MASK,
    show_length: bool = False,
) -> MaskResult:
    """Mask sensitive values in *env*.

    Args:
        env: The environment dict to process.
        sensitive_keys: Explicit set of keys to mask.  When *None* the
            built-in heuristic is used.
        mask: Replacement string for masked values.
        show_length: If *True* the mask encodes the original value length,
            e.g. ``"***"`` for a 3-character secret.
    """
    entries: List[MaskEntry] = []
    for key, value in env.items():
        if _is_sensitive(key, sensitive_keys):
            display = "*" * len(value) if show_length else mask
            entries.append(MaskEntry(key=key, original=value, masked=display, was_masked=True))
        else:
            entries.append(MaskEntry(key=key, original=value, masked=value, was_masked=False))
    return MaskResult(entries=entries)
