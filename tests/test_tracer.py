import pytest
from envoy.tracer import trace_env, TraceResult, TraceEntry


@pytest.fixture
def sources():
    return {
        ".env.base": {"APP_NAME": "myapp", "DEBUG": "false", "PORT": "8000"},
        ".env.local": {"DEBUG": "true", "SECRET": "abc123"},
        ".env.override": {"PORT": "9000"},
    }


def test_trace_returns_trace_result(sources):
    result = trace_env(sources)
    assert isinstance(result, TraceResult)


def test_sources_recorded(sources):
    result = trace_env(sources)
    assert result.sources == list(sources.keys())


def test_active_env_contains_final_values(sources):
    result = trace_env(sources)
    env = result.env
    assert env["DEBUG"] == "true"
    assert env["PORT"] == "9000"
    assert env["APP_NAME"] == "myapp"
    assert env["SECRET"] == "abc123"


def test_overridden_entries_captured(sources):
    result = trace_env(sources)
    overridden_keys = [e.key for e in result.overridden]
    assert "DEBUG" in overridden_keys
    assert "PORT" in overridden_keys


def test_non_overridden_key_not_in_overridden(sources):
    result = trace_env(sources)
    overridden_keys = [e.key for e in result.overridden]
    assert "APP_NAME" not in overridden_keys


def test_source_for_returns_correct_label(sources):
    result = trace_env(sources)
    assert result.source_for("DEBUG") == ".env.local"
    assert result.source_for("PORT") == ".env.override"
    assert result.source_for("APP_NAME") == ".env.base"


def test_source_for_missing_key_returns_none(sources):
    result = trace_env(sources)
    assert result.source_for("NONEXISTENT") is None


def test_overridden_entry_has_overridden_by_set(sources):
    result = trace_env(sources)
    debug_entries = [e for e in result.entries if e.key == "DEBUG"]
    overridden = [e for e in debug_entries if e.overridden_by is not None]
    assert len(overridden) == 1
    assert overridden[0].overridden_by == ".env.local"


def test_summary_string(sources):
    result = trace_env(sources)
    s = result.summary()
    assert "active" in s
    assert "shadowed" in s


def test_empty_sources_returns_empty_result():
    result = trace_env({})
    assert result.env == {}
    assert result.entries == []


def test_single_source_no_overrides():
    result = trace_env({".env": {"A": "1", "B": "2"}})
    assert len(result.overridden) == 0
    assert result.env == {"A": "1", "B": "2"}


def test_to_dict_on_entry():
    e = TraceEntry(key="K", value="v", source=".env", overridden_by=".env.local")
    d = e.to_dict()
    assert d["key"] == "K"
    assert d["overridden_by"] == ".env.local"
