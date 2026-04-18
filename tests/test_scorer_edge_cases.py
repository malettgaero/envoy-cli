"""Edge-case tests for envoy.scorer."""
from envoy.scorer import score_env


def test_score_points_never_negative():
    """Even with all deductions, points floor at 0."""
    env = {"db_key": ""}
    result = score_env(env, penalise_empty=True, penalise_lowercase=True, penalise_no_comment=True,
                       lines=["db_key=\n"])
    entry = result.entries[0]
    assert entry.points >= 0


def test_single_key_max_score_ten():
    env = {"HOST": "localhost"}
    result = score_env(env)
    assert result.max_score == 10


def test_percent_rounds_to_one_decimal():
    env = {"A": "", "B": "ok", "C": "ok"}
    result = score_env(env, penalise_empty=True, penalise_lowercase=False)
    assert isinstance(result.percent, float)
    assert result.percent == round(result.percent, 1)


def test_to_dict_on_entry():
    env = {"HOST": ""}
    result = score_env(env, penalise_empty=True)
    d = result.entries[0].to_dict()
    assert "key" in d
    assert "points" in d
    assert "deductions" in d


def test_no_lines_no_comment_penalty_applied():
    """When lines=None, no-comment penalty should not apply even if flag set."""
    env = {"HOST": "localhost"}
    result = score_env(env, lines=None, penalise_no_comment=True)
    entry = result.entries[0]
    # penalty only fires when lines are provided
    assert "no preceding comment" not in entry.deductions


def test_grade_boundaries():
    from envoy.scorer import ScoreResult, ScoreEntry
    def _make(total, maximum):
        return ScoreResult(entries=[], max_score=maximum, total_score=total)

    assert _make(90, 100).grade == "A"
    assert _make(75, 100).grade == "B"
    assert _make(60, 100).grade == "C"
    assert _make(40, 100).grade == "D"
    assert _make(39, 100).grade == "F"
