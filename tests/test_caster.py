"""Tests for envoy.caster."""
import pytest
from envoy.caster import cast_env, CastResult, CastEntry


@pytest.fixture()
def base_env():
    return {
        "DEBUG": "true",
        "PORT": "8080",
        "RATIO": "0.75",
        "NAME": "myapp",
        "ENABLED": "false",
        "RETRIES": "3",
        "EMPTY": "",
    }


def test_cast_returns_cast_result(base_env):
    result = cast_env(base_env)
    assert isinstance(result, CastResult)


def test_all_keys_present(base_env):
    result = cast_env(base_env)
    assert set(result.env.keys()) == set(base_env.keys())


def test_bool_true_cast(base_env):
    result = cast_env(base_env)
    assert result.env["DEBUG"] is True
    assert result.types["DEBUG"] == "bool"


def test_bool_false_cast(base_env):
    result = cast_env(base_env)
    assert result.env["ENABLED"] is False
    assert result.types["ENABLED"] == "bool"


def test_int_cast(base_env):
    result = cast_env(base_env)
    assert result.env["PORT"] == 8080
    assert isinstance(result.env["PORT"], int)
    assert result.types["PORT"] == "int"


def test_float_cast(base_env):
    result = cast_env(base_env)
    assert result.env["RATIO"] == pytest.approx(0.75)
    assert result.types["RATIO"] == "float"


def test_str_cast(base_env):
    result = cast_env(base_env)
    assert result.env["NAME"] == "myapp"
    assert result.types["NAME"] == "str"


def test_empty_string_is_str(base_env):
    result = cast_env(base_env)
    assert result.env["EMPTY"] == ""
    assert result.types["EMPTY"] == "str"


def test_int_not_cast_as_float():
    result = cast_env({"N": "42"})
    assert isinstance(result.env["N"], int)
    assert result.types["N"] == "int"


def test_yes_no_variants():
    result = cast_env({"A": "yes", "B": "no", "C": "on", "D": "off"})
    assert result.env["A"] is True
    assert result.env["B"] is False
    assert result.env["C"] is True
    assert result.env["D"] is False


def test_case_insensitive_bool():
    result = cast_env({"X": "TRUE", "Y": "False"})
    assert result.env["X"] is True
    assert result.env["Y"] is False


def test_summary_contains_type_counts(base_env):
    result = cast_env(base_env)
    s = result.summary()
    assert "bool=" in s
    assert "int=" in s
    assert "float=" in s
    assert "str=" in s


def test_to_dict_on_entry():
    entry = CastEntry(key="PORT", raw="9000", cast_value=9000, cast_type="int")
    d = entry.to_dict()
    assert d["key"] == "PORT"
    assert d["cast_value"] == 9000
    assert d["cast_type"] == "int"


def test_empty_env_returns_empty_result():
    result = cast_env({})
    assert result.env == {}
    assert result.summary() == "0 keys cast"
