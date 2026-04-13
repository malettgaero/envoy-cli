"""Tests for envoy.templater."""
import pytest

from envoy.templater import TemplateError, render_env


def test_no_placeholders_returns_unchanged():
    env = {"HOST": "localhost", "PORT": "5432"}
    result = render_env(env, {})
    assert result.rendered == env
    assert result.resolved == []
    assert result.unresolved == []
    assert result.is_complete


def test_single_placeholder_resolved():
    env = {"DSN": "postgres://{{ DB_HOST }}/mydb"}
    ctx = {"DB_HOST": "db.internal"}
    result = render_env(env, ctx)
    assert result.rendered["DSN"] == "postgres://db.internal/mydb"
    assert "DB_HOST" in result.resolved
    assert result.unresolved == []


def test_multiple_placeholders_in_one_value():
    env = {"URL": "http://{{ HOST }}:{{ PORT }}/api"}
    ctx = {"HOST": "example.com", "PORT": "8080"}
    result = render_env(env, ctx)
    assert result.rendered["URL"] == "http://example.com:8080/api"
    assert set(result.resolved) == {"HOST", "PORT"}


def test_unresolved_placeholder_kept_as_is():
    env = {"ENDPOINT": "http://{{ HOST }}/path"}
    result = render_env(env, {})
    assert result.rendered["ENDPOINT"] == "http://{{ HOST }}/path"
    assert "HOST" in result.unresolved
    assert not result.is_complete


def test_strict_mode_raises_on_unresolved():
    env = {"KEY": "{{ MISSING }}"}
    with pytest.raises(TemplateError) as exc_info:
        render_env(env, {}, strict=True)
    assert "MISSING" in str(exc_info.value)
    assert exc_info.value.missing == ["MISSING"]


def test_strict_mode_passes_when_all_resolved():
    env = {"KEY": "{{ VAL }}"}
    result = render_env(env, {"VAL": "hello"}, strict=True)
    assert result.rendered["KEY"] == "hello"


def test_partial_context_resolves_available_keys():
    env = {"A": "{{ X }}-{{ Y }}"}
    result = render_env(env, {"X": "foo"})
    assert result.rendered["A"] == "foo-{{ Y }}"
    assert "X" in result.resolved
    assert "Y" in result.unresolved


def test_whitespace_inside_placeholder_tokens():
    env = {"VAL": "{{  SPACED  }}"}
    ctx = {"SPACED": "ok"}
    result = render_env(env, ctx)
    assert result.rendered["VAL"] == "ok"


def test_render_empty_env():
    result = render_env({}, {"X": "1"})
    assert result.rendered == {}
    assert result.is_complete


def test_duplicate_placeholders_deduplicated():
    env = {"A": "{{ X }}", "B": "{{ X }}_suffix"}
    result = render_env(env, {})
    assert result.unresolved.count("X") == 1
