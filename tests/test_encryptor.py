"""Tests for envoy.encryptor."""

import pytest

pytest.importorskip("cryptography", reason="cryptography package required")

from envoy.encryptor import (
    EncryptionError,
    EncryptResult,
    decrypt_values,
    encrypt_values,
)

PASS = "super-secret-passphrase"


def _env(**kwargs: str):
    return dict(kwargs)


# ---------------------------------------------------------------------------
# encrypt_values
# ---------------------------------------------------------------------------

def test_encrypt_returns_enc_prefix():
    env = _env(DB_PASS="hunter2", API_KEY="abc123")
    result = encrypt_values(env, ["DB_PASS"], PASS)
    assert result.encrypted["DB_PASS"].startswith("enc:")


def test_encrypt_leaves_other_keys_unchanged():
    env = _env(DB_PASS="hunter2", API_KEY="abc123")
    result = encrypt_values(env, ["DB_PASS"], PASS)
    assert result.encrypted["API_KEY"] == "abc123"


def test_encrypt_multiple_keys():
    env = _env(A="val_a", B="val_b", C="plain")
    result = encrypt_values(env, ["A", "B"], PASS)
    assert result.encrypted["A"].startswith("enc:")
    assert result.encrypted["B"].startswith("enc:")
    assert result.encrypted["C"] == "plain"
    assert result.count == 3  # total keys in dict


def test_encrypt_skips_missing_keys():
    env = _env(PRESENT="value")
    result = encrypt_values(env, ["PRESENT", "MISSING"], PASS)
    assert "MISSING" in result.skipped
    assert "PRESENT" not in result.skipped


def test_encrypt_empty_keys_list_leaves_env_unchanged():
    env = _env(FOO="bar")
    result = encrypt_values(env, [], PASS)
    assert result.encrypted == env
    assert result.skipped == []


# ---------------------------------------------------------------------------
# decrypt_values
# ---------------------------------------------------------------------------

def test_roundtrip_single_key():
    env = _env(SECRET="my-password")
    encrypted = encrypt_values(env, ["SECRET"], PASS)
    decrypted = decrypt_values(encrypted.encrypted, PASS)
    assert decrypted["SECRET"] == "my-password"


def test_roundtrip_mixed_env():
    env = _env(SECRET="s3cr3t", PLAIN="visible")
    encrypted = encrypt_values(env, ["SECRET"], PASS)
    decrypted = decrypt_values(encrypted.encrypted, PASS)
    assert decrypted["SECRET"] == "s3cr3t"
    assert decrypted["PLAIN"] == "visible"


def test_decrypt_wrong_passphrase_raises():
    env = _env(SECRET="value")
    encrypted = encrypt_values(env, ["SECRET"], PASS)
    with pytest.raises(EncryptionError, match="SECRET"):
        decrypt_values(encrypted.encrypted, "wrong-passphrase")


def test_decrypt_non_prefixed_values_pass_through():
    env = _env(FOO="plain", BAR="also-plain")
    result = decrypt_values(env, PASS)
    assert result == env


def test_decrypt_empty_env_returns_empty():
    assert decrypt_values({}, PASS) == {}
