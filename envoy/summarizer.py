from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class SummaryEntry:
    key: str
    value_length: int
    is_empty: bool
    is_secret: bool
    category: str

    def to_dict(self) -> Dict:
        return {
            "key": self.key,
            "value_length": self.value_length,
            "is_empty": self.is_empty,
            "is_secret": self.is_secret,
            "category": self.category,
        }


@dataclass
class SummaryResult:
    entries: List[SummaryEntry]
    total: int
    empty_count: int
    secret_count: int
    categories: Dict[str, int]

    def overview(self) -> str:
        lines = [
            f"Total keys   : {self.total}",
            f"Empty values : {self.empty_count}",
            f"Secret keys  : {self.secret_count}",
            "Categories   :",
        ]
        for cat, count in sorted(self.categories.items()):
            lines.append(f"  {cat}: {count}")
        return "\n".join(lines)


_SECRET_HINTS = ("password", "secret", "token", "key", "api", "auth", "pwd", "pass")

_CATEGORY_RULES = [
    ("database", ("db", "database", "postgres", "mysql", "mongo", "redis")),
    ("secret",   ("password", "secret", "token", "api_key", "auth", "pwd", "pass")),
    ("network",  ("host", "port", "url", "uri", "endpoint", "domain")),
    ("feature",  ("enable", "disable", "feature", "flag")),
]


def _categorize(key: str) -> str:
    lower = key.lower()
    for category, hints in _CATEGORY_RULES:
        if any(h in lower for h in hints):
            return category
    return "general"


def summarize_env(env: Dict[str, str]) -> SummaryResult:
    entries: List[SummaryEntry] = []
    categories: Dict[str, int] = {}

    for key in sorted(env):
        value = env[key]
        lower = key.lower()
        is_secret = any(h in lower for h in _SECRET_HINTS)
        is_empty = value.strip() == ""
        cat = _categorize(key)
        categories[cat] = categories.get(cat, 0) + 1
        entries.append(SummaryEntry(
            key=key,
            value_length=len(value),
            is_empty=is_empty,
            is_secret=is_secret,
            category=cat,
        ))

    return SummaryResult(
        entries=entries,
        total=len(entries),
        empty_count=sum(1 for e in entries if e.is_empty),
        secret_count=sum(1 for e in entries if e.is_secret),
        categories=categories,
    )
