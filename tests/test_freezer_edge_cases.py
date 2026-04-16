from envoy.freezer import freeze_env, verify_env, _checksum


def test_empty_env_produces_checksum():
    result = freeze_env({})
    assert len(result.checksum) == 64


def test_checksum_order_independent():
    a = {"X": "1", "Y": "2"}
    b = {"Y": "2", "X": "1"}
    assert _checksum(a) == _checksum(b)


def test_verify_empty_env_against_empty_checksum():
    frozen = freeze_env({})
    result = verify_env({}, frozen.checksum)
    assert result.passed


def test_verify_empty_env_against_nonempty_checksum():
    frozen = freeze_env({"A": "1"})
    result = verify_env({}, frozen.checksum)
    assert not result.passed


def test_freeze_result_env_is_copy():
    env = {"A": "1"}
    result = freeze_env(env)
    env["B"] = "2"
    assert "B" not in result.env


def test_freeze_result_passed_when_no_violations():
    result = freeze_env({"K": "v"})
    assert result.passed
    assert result.violations == []
