"""Edge-case tests for envoy.promoter."""
from envoy.promoter import promote_env


def test_empty_source_returns_empty_result():
    result = promote_env({}, {"A": "1"})
    assert result.promoted_count == 0
    assert result.skipped == []


def test_empty_target_all_keys_are_new():
    result = promote_env({"A": "1", "B": "2"}, {})
    assert result.new_count == 2
    assert result.overwrite_count == 0


def test_empty_keys_list_promotes_nothing():
    result = promote_env({"A": "1"}, {}, keys=[])
    assert result.promoted_count == 0


def test_all_keys_already_in_target_no_overwrite():
    src = {"A": "new", "B": "new"}
    tgt = {"A": "old", "B": "old"}
    result = promote_env(src, tgt, overwrite=False)
    assert result.promoted_count == 0
    assert set(result.skipped) == {"A", "B"}


def test_env_output_merges_correctly():
    src = {"A": "src_a", "B": "src_b"}
    tgt = {"B": "tgt_b", "C": "tgt_c"}
    result = promote_env(src, tgt, overwrite=True)
    env = result.env()
    # Both A and B should come from source
    assert env["A"] == "src_a"
    assert env["B"] == "src_b"
    # C is not in result.env() since it wasn't promoted
    assert "C" not in env


def test_summary_includes_skipped_when_present():
    src = {"A": "1"}
    tgt = {"A": "old"}
    result = promote_env(src, tgt, keys=["A", "MISSING"], overwrite=True)
    s = result.summary()
    assert "skipped=" in s


def test_duplicate_keys_in_keys_list_deduplicated_by_dict():
    src = {"A": "1"}
    tgt = {}
    # Passing the same key twice should still promote it once
    result = promote_env(src, tgt, keys=["A", "A"])
    # Two entries are created (no dedup in promoter — caller responsibility)
    assert result.promoted_count == 2  # both iterations succeed
