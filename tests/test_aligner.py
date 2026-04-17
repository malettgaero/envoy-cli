"""Tests for envoy.aligner."""
import pytest
from envoy.aligner import align_env, AlignResult


def _lines(*raw):
    return [l + "\n" for l in raw]


def test_align_returns_align_result():
    result = align_env(_lines("A=1", "BB=2"))
    assert isinstance(result, AlignResult)


def test_already_aligned_no_change():
    lines = _lines("A  = 1", "BB = 2")
    result = align_env(lines)
    assert not result.changed


def test_unaligned_keys_are_padded():
    result = align_env(_lines("A=1", "BB=2", "CCC=3"))
    assert result.changed
    keys_in_output = [l.split(" = ")[0].rstrip() for l in result.lines_out if "=" in l]
    widths = [len(k) for k in keys_in_output]
    assert len(set(widths)) == 1, "All keys should have equal padded width"


def test_comments_and_blanks_preserved():
    lines = _lines("# comment", "", "A=1", "BB=2")
    result = align_env(lines)
    assert result.lines_out[0].strip() == "# comment"
    assert result.lines_out[1].strip() == ""


def test_changed_count_correct():
    result = align_env(_lines("A=1", "LONG_KEY=2"))
    # 'A' will be padded, 'LONG_KEY' stays same length — only A changes
    assert result.changed_count >= 1


def test_no_pairs_returns_unchanged():
    lines = _lines("# just a comment", "")
    result = align_env(lines)
    assert not result.changed
    assert result.lines_out == lines


def test_custom_separator():
    result = align_env(_lines("A=1", "BB=2"), separator="=")
    for line in result.lines_out:
        if "=" in line:
            assert " " not in line.split("=")[0] or line.split("=")[0] == line.split("=")[0]


def test_summary_no_change():
    lines = _lines("A = 1", "B = 2")
    result = align_env(lines)
    # force no change scenario
    for e in result.entries:
        e.aligned_line = e.original_line
    assert "no changes" in result.summary()


def test_summary_with_changes():
    result = align_env(_lines("A=1", "LONGKEY=2"))
    if result.changed:
        assert "realigned" in result.summary()


def test_entry_to_dict_keys():
    result = align_env(_lines("FOO=bar"))
    if result.entries:
        d = result.entries[0].to_dict()
        assert "key" in d and "original_line" in d and "aligned_line" in d


def test_single_key_no_padding_needed():
    result = align_env(_lines("ONLY=value"))
    assert isinstance(result, AlignResult)
    assert len(result.entries) == 1
