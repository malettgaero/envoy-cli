"""Expiry checker — flags env keys whose values look like expired or near-expiry dates."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List, Optional
import re

_DATE_PATTERNS = [
    r"^(\d{4})-(\d{2})-(\d{2})$",
    r"^(\d{2})/(\d{2})/(\d{4})$",
]


def _parse_date(value: str) -> Optional[date]:
    for pat in _DATE_PATTERNS:
        m = re.match(pat, value.strip())
        if m:
            parts = [int(x) for x in m.groups()]
            try:
                if pat.startswith(r"^(\d{4})"):
                    return date(parts[0], parts[1], parts[2])
                else:
                    return date(parts[2], parts[1], parts[0])
            except ValueError:
                return None
    return None


@dataclass
class ExpiryEntry:
    key: str
    value: str
    parsed_date: date
    days_remaining: int
    expired: bool

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "parsed_date": self.parsed_date.isoformat(),
            "days_remaining": self.days_remaining,
            "expired": self.expired,
        }


@dataclass
class ExpiryResult:
    entries: List[ExpiryEntry] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def expired(self) -> List[ExpiryEntry]:
        return [e for e in self.entries if e.expired]

    @property
    def expiring_soon(self) -> List[ExpiryEntry]:
        return [e for e in self.entries if not e.expired and e.days_remaining <= 30]

    @property
    def passed(self) -> bool:
        return len(self.expired) == 0

    def summary(self) -> str:
        parts = [f"{len(self.entries)} date key(s) checked"]
        if self.expired:
            parts.append(f"{len(self.expired)} expired")
        if self.expiring_soon:
            parts.append(f"{len(self.expiring_soon)} expiring within 30 days")
        return ", ".join(parts)


def check_expiry(
    env: Dict[str, str],
    keys: Optional[List[str]] = None,
    reference_date: Optional[date] = None,
) -> ExpiryResult:
    today = reference_date or date.today()
    result = ExpiryResult()
    targets = {k: v for k, v in env.items() if keys is None or k in (keys or [])}
    for key, value in sorted(targets.items()):
        parsed = _parse_date(value)
        if parsed is None:
            if keys and key in keys:
                result.skipped.append(key)
            continue
        delta = (parsed - today).days
        result.entries.append(
            ExpiryEntry(
                key=key,
                value=value,
                parsed_date=parsed,
                days_remaining=delta,
                expired=delta < 0,
            )
        )
    return result
