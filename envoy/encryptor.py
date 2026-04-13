"""Simple symmetric encryption/decryption for .env secret values."""

from __future__ import annotations

import base64
import hashlib
import os
from dataclasses import dataclass, field
from typing import Dict, List


class EncryptionError(Exception):
    """Raised when encryption or decryption fails."""

    def __str__(self) -> str:  # pragma: no cover
        return f"EncryptionError: {self.args[0]}"


try:
    from cryptography.fernet import Fernet, InvalidToken
    _CRYPTO_AVAILABLE = True
except ImportError:  # pragma: no cover
    _CRYPTO_AVAILABLE = False


@dataclass
class EncryptResult:
    encrypted: Dict[str, str] = field(default_factory=dict)
    skipped: List[str] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.encrypted)


def _derive_key(passphrase: str) -> bytes:
    """Derive a 32-byte Fernet-compatible key from a passphrase."""
    digest = hashlib.sha256(passphrase.encode()).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_values(
    env: Dict[str, str],
    keys_to_encrypt: List[str],
    passphrase: str,
) -> EncryptResult:
    """Return a copy of *env* with selected keys encrypted.

    Values are prefixed with ``enc:`` so callers can identify ciphertext.
    Keys not present in *env* are added to ``EncryptResult.skipped``.
    """
    if not _CRYPTO_AVAILABLE:
        raise EncryptionError(
            "'cryptography' package is required. Install with: pip install cryptography"
        )

    fernet = Fernet(_derive_key(passphrase))
    result = EncryptResult(encrypted=dict(env))

    for key in keys_to_encrypt:
        if key not in env:
            result.skipped.append(key)
            continue
        raw = env[key].encode()
        token = fernet.encrypt(raw).decode()
        result.encrypted[key] = f"enc:{token}"

    return result


def decrypt_values(
    env: Dict[str, str],
    passphrase: str,
) -> Dict[str, str]:
    """Decrypt all ``enc:``-prefixed values in *env* and return the result."""
    if not _CRYPTO_AVAILABLE:
        raise EncryptionError(
            "'cryptography' package is required. Install with: pip install cryptography"
        )

    fernet = Fernet(_derive_key(passphrase))
    out: Dict[str, str] = {}

    for key, value in env.items():
        if value.startswith("enc:"):
            token = value[4:].encode()
            try:
                out[key] = fernet.decrypt(token).decode()
            except Exception as exc:
                raise EncryptionError(f"Failed to decrypt key '{key}': {exc}") from exc
        else:
            out[key] = value

    return out
