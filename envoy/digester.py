"""Compute per-key digests (hashes) for an env dict."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DigestEntry:
    key: str
    value: str
    algorithm: str
    digest: str

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "algorithm": self.algorithm,
            "digest": self.digest,
        }


@dataclass
class DigestResult:
    entries: List[DigestEntry] = field(default_factory=list)
    algorithm: str = "sha256"

    def digest_for(self, key: str) -> Optional[str]:
        for e in self.entries:
            if e.key == key:
                return e.digest
        return None

    def as_dict(self) -> Dict[str, str]:
        return {e.key: e.digest for e in self.entries}

    def summary(self) -> str:
        return f"{len(self.entries)} key(s) digested with {self.algorithm}"


_SUPPORTED = {"md5", "sha1", "sha256", "sha512"}


class DigestError(Exception):
    pass


def digest_env(
    env: Dict[str, str],
    algorithm: str = "sha256",
    keys: Optional[List[str]] = None,
) -> DigestResult:
    """Return a DigestResult with a hash of each value."""
    algo = algorithm.lower()
    if algo not in _SUPPORTED:
        raise DigestError(f"Unsupported algorithm '{algorithm}'. Choose from: {', '.join(sorted(_SUPPORTED))}")

    targets = keys if keys is not None else sorted(env.keys())
    entries: List[DigestEntry] = []

    for key in targets:
        if key not in env:
            continue
        raw = env[key].encode()
        digest = hashlib.new(algo, raw).hexdigest()
        entries.append(DigestEntry(key=key, value=env[key], algorithm=algo, digest=digest))

    return DigestResult(entries=entries, algorithm=algo)
