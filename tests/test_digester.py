"""Tests for envoy.digester."""
import hashlib
import pytest
from envoy.digester import digest_env, DigestError


@pytest.fixture
def base_env():
    return {"API_KEY": "secret", "HOST": "localhost", "PORT": "8080"}


def test_digest_returns_result(base_env):
    result = digest_env(base_env)
    assert result is not None
    assert len(result.entries) == 3


def test_default_algorithm_is_sha256(base_env):
    result = digest_env(base_env)
    assert result.algorithm == "sha256"


def test_digest_value_matches_hashlib(base_env):
    result = digest_env(base_env)
    expected = hashlib.sha256(b"secret").hexdigest()
    assert result.digest_for("API_KEY") == expected


def test_md5_algorithm(base_env):
    result = digest_env(base_env, algorithm="md5")
    expected = hashlib.md5(b"localhost").hexdigest()
    assert result.digest_for("HOST") == expected


def test_sha512_algorithm(base_env):
    result = digest_env(base_env, algorithm="sha512")
    entry = result.entries[0]
    assert len(entry.digest) == 128


def test_unsupported_algorithm_raises(base_env):
    with pytest.raises(DigestError, match="Unsupported"):
        digest_env(base_env, algorithm="crc32")


def test_keys_filter_limits_output(base_env):
    result = digest_env(base_env, keys=["HOST"])
    assert len(result.entries) == 1
    assert result.entries[0].key == "HOST"


def test_missing_key_in_filter_skipped(base_env):
    result = digest_env(base_env, keys=["HOST", "MISSING"])
    assert len(result.entries) == 1


def test_as_dict_returns_key_digest_map(base_env):
    result = digest_env(base_env, keys=["PORT"])
    d = result.as_dict()
    assert "PORT" in d
    assert d["PORT"] == hashlib.sha256(b"8080").hexdigest()


def test_summary_string(base_env):
    result = digest_env(base_env)
    assert "3" in result.summary()
    assert "sha256" in result.summary()


def test_to_dict_on_entry(base_env):
    result = digest_env(base_env, keys=["API_KEY"])
    d = result.entries[0].to_dict()
    assert d["key"] == "API_KEY"
    assert d["algorithm"] == "sha256"
    assert "digest" in d


def test_empty_env_returns_empty_result():
    result = digest_env({})
    assert result.entries == []
    assert result.as_dict() == {}
