"""Type-checking module for .env values against declared type hints."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_SUPPORTED_TYPES = {"str", "int", "float", "bool", "url", "email"}

_URL_RE = re.compile(
    r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE
)
_EMAIL_RE = re.compile(
    r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
)
_BOOL_TRUTHY = {"true", "1", "yes", "on"}
_BOOL_FALSY = {"false", "0", "no", "off"}


@dataclass
class TypeViolation:
    key: str
    value: str
    expected_type: str
    message: str

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "expected_type": self.expected_type,
            "message": self.message,
        }


@dataclass
class TypeCheckResult:
    violations: List[TypeViolation] = field(default_factory=list)
    unknown_types: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.violations) == 0

    def summary(self) -> str:
        if self.passed:
            return "All values match declared types."
        lines = [f"{len(self.violations)} type violation(s) found:"]
        for v in self.violations:
            lines.append(f"  {v.key}: expected {v.expected_type} — {v.message}")
        return "\n".join(lines)


def _check_value(key: str, value: str, type_hint: str) -> Optional[TypeViolation]:
    t = type_hint.strip().lower()
    if t == "str":
        return None
    if t == "int":
        try:
            int(value)
        except ValueError:
            return TypeViolation(key, value, t, f"'{value}' is not a valid integer")
    elif t == "float":
        try:
            float(value)
        except ValueError:
            return TypeViolation(key, value, t, f"'{value}' is not a valid float")
    elif t == "bool":
        if value.lower() not in _BOOL_TRUTHY | _BOOL_FALSY:
            return TypeViolation(
                key, value, t,
                f"'{value}' is not a valid bool (use true/false/1/0/yes/no/on/off)"
            )
    elif t == "url":
        if not _URL_RE.match(value):
            return TypeViolation(key, value, t, f"'{value}' is not a valid URL")
    elif t == "email":
        if not _EMAIL_RE.match(value):
            return TypeViolation(key, value, t, f"'{value}' is not a valid email address")
    return None


def typecheck_env(
    env: Dict[str, str],
    type_hints: Dict[str, str],
) -> TypeCheckResult:
    """Check env values against a mapping of key -> type hint."""
    result = TypeCheckResult()
    for key, type_hint in type_hints.items():
        t = type_hint.strip().lower()
        if t not in _SUPPORTED_TYPES:
            result.unknown_types.append(type_hint)
            continue
        if key not in env:
            continue
        violation = _check_value(key, env[key], t)
        if violation:
            result.violations.append(violation)
    return result
