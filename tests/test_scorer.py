"""Tests for envoy.scorer."""
import pytest
from envoy.scorer import score_env, ScoreResult


@pytest.fixture
def base_env():
    return {
        "DATABASE_URL": "postgres://localhost/db",
        "SECRET_KEY": "supersecret",
        "DEBUG": "true",
    }


def test_score_returns_score_result(base_env):
    result = score_env(base_env)
    assert isinstance(result, ScoreResult)


def test_all_clean_keys_get_full_points(base_env):
    result = score_env(base_env, penalise_empty=True, penalise_lowercase=True)
    for entry in result.entries:
        assert entry.points == 10
        assert entry.deductions == []


def test_empty_value_deducted():
    env = {"API_KEY": ""}
    result = score_env(env, penalise_empty=True)
    entry = result.entries[0]
    assert entry.points == 6
    assert "empty value" in entry.deductions


def test_lowercase_key_deducted():
    env = {"db_host": "localhost"}
    result = score_env(env, penalise_lowercase=True)
    entry = result.entries[0]
    assert entry.points == 8
    assert "lowercase key" in entry.deductions


def test_both_deductions_applied():
    env = {"db_host": ""}
    result = score_env(env, penalise_empty=True, penalise_lowercase=True)
    entry = result.entries[0]
    assert entry.points == 4
    assert len(entry.deductions) == 2


def test_max_score_is_keys_times_ten(base_env):
    result = score_env(base_env)
    assert result.max_score == len(base_env) * 10


def test_total_score_sums_entries(base_env):
    result = score_env(base_env)
    assert result.total_score == sum(e.points for e in result.entries)


def test_percent_perfect():
    env = {"HOST": "localhost"}
    result = score_env(env)
    assert result.percent == 100.0


def test_grade_a_for_high_score():
    env = {"HOST": "localhost", "PORT": "8080"}
    result = score_env(env)
    assert result.grade == "A"


def test_grade_f_for_all_empty_lowercase():
    env = {"a": "", "b": ""}
    result = score_env(env, penalise_empty=True, penalise_lowercase=True)
    assert result.grade in ("D", "F")


def test_empty_env_returns_100_percent():
    result = score_env({})
    assert result.percent == 100.0
    assert result.grade == "A"


def test_entries_sorted_alphabetically():
    env = {"ZEBRA": "z", "ALPHA": "a", "MIDDLE": "m"}
    result = score_env(env)
    keys = [e.key for e in result.entries]
    assert keys == sorted(keys)


def test_summary_string_format(base_env):
    result = score_env(base_env)
    s = result.summary()
    assert "Score:" in s
    assert "Grade:" in s


def test_no_comment_penalty_applied():
    env = {"HOST": "localhost"}
    lines = ["HOST=localhost\n"]
    result = score_env(env, lines=lines, penalise_no_comment=True)
    entry = result.entries[0]
    assert "no preceding comment" in entry.deductions


def test_comment_before_key_no_penalty():
    env = {"HOST": "localhost"}
    lines = ["# the host\n", "HOST=localhost\n"]
    result = score_env(env, lines=lines, penalise_no_comment=True)
    entry = result.entries[0]
    assert "no preceding comment" not in entry.deductions
