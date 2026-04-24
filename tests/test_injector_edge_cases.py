"""Edge-case tests for envoy.injector."""
from envoy.injector import inject_env


def test_empty_base_all_keys_are_new():
    source = {"A": "1", "B": "2"}
    result = inject_env({}, source)
    assert result.injected_count == 2
    assert result.overwritten_count == 0


def test_empty_source_no_injection():
    base = {"A": "1"}
    result = inject_env(base, {})
    assert result.injected_count == 0
    assert result.env == base


def test_both_empty_returns_empty_env():
    result = inject_env({}, {})
    assert result.env == {}
    assert result.injected_count == 0


def test_keys_filter_empty_list_injects_nothing():
    result = inject_env({"A": "1"}, {"B": "2"}, keys=[])
    assert result.injected_count == 0


def test_inject_preserves_unrelated_base_keys():
    base = {"KEEP": "yes", "ALSO": "keep"}
    source = {"NEW": "value"}
    result = inject_env(base, source)
    assert result.env["KEEP"] == "yes"
    assert result.env["ALSO"] == "keep"


def test_inject_value_with_equals_sign():
    base = {}
    source = {"TOKEN": "abc=def=ghi"}
    result = inject_env(base, source)
    assert result.env["TOKEN"] == "abc=def=ghi"


def test_inject_empty_value():
    base = {"KEY": "old"}
    source = {"KEY": ""}
    result = inject_env(base, source)
    assert result.env["KEY"] == ""
    assert result.overwritten_count == 1


def test_overwritten_count_zero_when_all_new():
    result = inject_env({}, {"X": "1", "Y": "2"})
    assert result.overwritten_count == 0


def test_base_env_property_reflects_original():
    base = {"A": "original"}
    source = {"A": "replaced"}
    result = inject_env(base, source)
    assert result.base_env["A"] == "original"
    assert result.env["A"] == "replaced"
