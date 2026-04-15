"""Classify .env keys by their likely purpose based on naming patterns."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Pattern groups: (category, substrings that trigger it)
_RULES: List[tuple[str, List[str]]] = [
    ("secret",   ["SECRET", "PASSWORD", "PASSWD", "TOKEN", "API_KEY", "PRIVATE_KEY", "CREDENTIALS"]),
    ("database", ["DB_", "DATABASE", "POSTGRES", "MYSQL", "MONGO", "REDIS", "SQLITE"]),
    ("network",  ["HOST", "PORT", "URL", "URI", "ENDPOINT", "DOMAIN", "ADDR"]),
    ("feature",  ["ENABLE_", "DISABLE_", "FEATURE_", "FLAG_"]),
    ("logging",  ["LOG", "DEBUG", "VERBOSE", "TRACE"]),
    ("auth",     ["AUTH", "JWT", "OAUTH", "SSO", "SESSION", "COOKIE"]),
    ("storage",  ["BUCKET", "S3", "STORAGE", "BLOB", "DISK", "PATH", "DIR"]),
    ("email",    ["SMTP", "MAIL", "EMAIL", "SENDGRID", "MAILGUN"]),
]

_DEFAULT_CATEGORY = "general"


@dataclass
class ClassifyEntry:
    key: str
    value: str
    category: str

    def to_dict(self) -> Dict[str, str]:
        return {"key": self.key, "value": self.value, "category": self.category}


@dataclass
class ClassifyResult:
    entries: List[ClassifyEntry] = field(default_factory=list)

    def by_category(self) -> Dict[str, List[ClassifyEntry]]:
        """Return entries grouped by category, sorted by category name."""
        groups: Dict[str, List[ClassifyEntry]] = {}
        for entry in self.entries:
            groups.setdefault(entry.category, []).append(entry)
        return dict(sorted(groups.items()))

    def category_for(self, key: str) -> Optional[str]:
        for entry in self.entries:
            if entry.key == key:
                return entry.category
        return None

    def summary(self) -> str:
        groups = self.by_category()
        lines = [f"{cat}: {len(items)} key(s)" for cat, items in groups.items()]
        return "\n".join(lines) if lines else "No keys to classify."


def _classify_key(key: str) -> str:
    upper = key.upper()
    for category, patterns in _RULES:
        if any(p in upper for p in patterns):
            return category
    return _DEFAULT_CATEGORY


def classify_env(env: Dict[str, str]) -> ClassifyResult:
    """Classify every key in *env* and return a ClassifyResult."""
    entries = [
        ClassifyEntry(key=k, value=v, category=_classify_key(k))
        for k, v in env.items()
    ]
    entries.sort(key=lambda e: e.key)
    return ClassifyResult(entries=entries)
