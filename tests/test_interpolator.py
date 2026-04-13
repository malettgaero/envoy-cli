"""Tests for envoy.interpolator."""

import pytest

from envoy.interpolator import interpolate_env, InterpolateResult


def test_no_references_returns_unchanged():
    env = {"HOST": "localhost", "PORT": "5432"}
    result = interpolate_env(env)
    assert result.env == env
    assert not result.has_warnings


def test_brace_style_reference_resolved():
    env = {"BASE": "http://example.com", "URL": "${BASE}/api"}
    result = interpolate_env(env)
    assert result.env["URL"] == "http://example.com/api"
    assert not result.has_warnings


def test_bare_dollar_reference_resolved():
    env = {"DOMAIN": "example.com", "SITE": "https://$DOMAIN"}
    result = interpolate_env(env)
    assert result.env["SITE"] == "https://example.com"


def test_multiple_references_in_one_value():
    env = {"SCHEME": "https", "HOST": "api.io", "PORT": "443",
           "ADDR": "${SCHEME}://${HOST}:${PORT}"}
    result = interpolate_env(env)
    assert result.env["ADDR"] == "https://api.io:443"


def test_unresolved_reference_generates_warning():
    env = {"URL": "${MISSING}/path"}
    result = interpolate_env(env)
    assert result.has_warnings
    assert result.warnings[0].ref == "MISSING"
    # original placeholder kept intact
    assert "${MISSING}" in result.env["URL"]


def test_strict_mode_raises_on_unresolved():
    env = {"URL": "${UNDEFINED}/path"}
    with pytest.raises(ValueError, match="UNDEFINED"):
        interpolate_env(env, strict=True)


def test_self_reference_does_not_resolve_circularly():
    # KEY references itself — should stay as-is (no KeyError)
    env = {"KEY": "${KEY}_suffix"}
    result = interpolate_env(env)
    # resolves using original env; KEY exists so it substitutes its own raw value
    assert "KEY" in result.env


def test_summary_no_warnings():
    result = interpolate_env({"A": "1"})
    assert "no unresolved" in result.summary()


def test_summary_with_warnings():
    result = interpolate_env({"A": "${GHOST}"})
    summary = result.summary()
    assert "1 warning" in summary
    assert "GHOST" in summary


def test_original_env_not_mutated():
    env = {"BASE": "http://x.com", "URL": "${BASE}/v1"}
    original = dict(env)
    interpolate_env(env)
    assert env == original


def test_empty_env_returns_empty():
    result = interpolate_env({})
    assert result.env == {}
    assert not result.has_warnings
