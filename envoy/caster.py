"""Cast .env values to their inferred Python types."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class CastEntry:
    key: str
    raw: str
    cast_value: Any
    cast_type: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "raw": self.raw,
            "cast_value": self.cast_value,
            "cast_type": self.cast_type,
        }


@dataclass
class CastResult:
    entries: List[CastEntry] = field(default_factory=list)

    @property
    def env(self) -> Dict[str, Any]:
        """Return a dict of key -> cast Python value."""
        return {e.key: e.cast_value for e in self.entries}

    @property
    def types(self) -> Dict[str, str]:
        """Return a dict of key -> inferred type name."""
        return {e.key: e.cast_type for e in self.entries}

    def summary(self) -> str:
        counts: Dict[str, int] = {}
        for e in self.entries:
            counts[e.cast_type] = counts.get(e.cast_type, 0) + 1
        parts = ", ".join(f"{t}={n}" for t, n in sorted(counts.items()))
        return f"{len(self.entries)} key(s) cast: {parts}" if parts else "0 keys cast"


_TRUE_VALUES = {"true", "yes", "1", "on"}
_FALSE_VALUES = {"false", "no", "0", "off"}


def _infer(raw: str) -> tuple[Any, str]:
    """Return (cast_value, type_name) for a raw string."""
    if raw == "":
        return raw, "str"

    lower = raw.lower()
    if lower in _TRUE_VALUES:
        return True, "bool"
    if lower in _FALSE_VALUES:
        return False, "bool"

    # Try int before float so "42" becomes int, not float.
    try:
        return int(raw), "int"
    except ValueError:
        pass

    try:
        return float(raw), "float"
    except ValueError:
        pass

    return raw, "str"


def cast_env(env: Dict[str, str]) -> CastResult:
    """Cast every value in *env* to its inferred Python type."""
    entries: List[CastEntry] = []
    for key in sorted(env):
        raw = env[key]
        value, type_name = _infer(raw)
        entries.append(CastEntry(key=key, raw=raw, cast_value=value, cast_type=type_name))
    return CastResult(entries=entries)
