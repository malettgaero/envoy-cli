"""Tokenize .env values into typed segments (literal, secret, reference)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
import re

TOKEN_LITERAL = "literal"
TOKEN_SECRET = "secret"
TOKEN_REFERENCE = "reference"

SECRET_PATTERN = re.compile(
    r"(password|secret|token|key|api|auth|pwd|pass)", re.IGNORECASE
)
REF_PATTERN = re.compile(r"\$\{([^}]+)\}|\$([A-Z_][A-Z0-9_]*)")


@dataclass
class Token:
    kind: str
    value: str

    def to_dict(self) -> dict:
        return {"kind": self.kind, "value": self.value}


@dataclass
class TokenizeEntry:
    key: str
    raw_value: str
    tokens: List[Token] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "raw_value": self.raw_value,
            "tokens": [t.to_dict() for t in self.tokens],
        }

    @property
    def has_references(self) -> bool:
        return any(t.kind == TOKEN_REFERENCE for t in self.tokens)

    @property
    def is_sensitive(self) -> bool:
        return any(t.kind == TOKEN_SECRET for t in self.tokens)


@dataclass
class TokenizeResult:
    entries: List[TokenizeEntry] = field(default_factory=list)

    def for_key(self, key: str) -> TokenizeEntry | None:
        return next((e for e in self.entries if e.key == key), None)

    @property
    def sensitive_keys(self) -> List[str]:
        return [e.key for e in self.entries if e.is_sensitive]

    @property
    def reference_keys(self) -> List[str]:
        return [e.key for e in self.entries if e.has_references]


def _tokenize_value(key: str, value: str) -> List[Token]:
    tokens: List[Token] = []
    remaining = value
    is_secret_key = bool(SECRET_PATTERN.search(key))
    while remaining:
        m = REF_PATTERN.search(remaining)
        if m:
            before = remaining[: m.start()]
            if before:
                kind = TOKEN_SECRET if is_secret_key else TOKEN_LITERAL
                tokens.append(Token(kind=kind, value=before))
            ref_name = m.group(1) or m.group(2)
            tokens.append(Token(kind=TOKEN_REFERENCE, value=ref_name))
            remaining = remaining[m.end() :]
        else:
            kind = TOKEN_SECRET if is_secret_key else TOKEN_LITERAL
            tokens.append(Token(kind=kind, value=remaining))
            break
    return tokens


def tokenize_env(env: dict) -> TokenizeResult:
    entries = []
    for key in sorted(env):
        value = env[key]
        tokens = _tokenize_value(key, value)
        entries.append(TokenizeEntry(key=key, raw_value=value, tokens=tokens))
    return TokenizeResult(entries=entries)
