"""Edge-case tests for envoy.duplicator."""
from envoy.duplicator import find_duplicates


def test_key_with_spaces_around_equals():
    lines = ["FOO = 1", "FOO = 2"]
    result = find_duplicates(lines)
    assert result.has_duplicates
    assert result.duplicates[0].key == "FOO"


def test_line_without_equals_is_skipped():
    lines = ["INVALID_LINE", "FOO=bar", "FOO=baz"]
    result = find_duplicates(lines)
    # Only FOO is a duplicate; INVALID_LINE must not cause errors
    assert len(result.duplicates) == 1
    assert result.duplicates[0].key == "FOO"


def test_value_containing_equals_does_not_split_key():
    lines = ["URL=http://a.com?x=1", "URL=http://b.com?x=2"]
    result = find_duplicates(lines)
    assert result.has_duplicates
    assert result.duplicates[0].key == "URL"


def test_result_sorted_by_first_occurrence():
    lines = ["B=1", "A=2", "B=3", "A=4"]
    result = find_duplicates(lines)
    # B first appears on line 1, A first appears on line 2
    assert result.duplicates[0].key == "B"
    assert result.duplicates[1].key == "A"


def test_only_blank_lines_returns_no_duplicates():
    lines = ["", "   ", ""]
    result = find_duplicates(lines)
    assert not result.has_duplicates


def test_has_duplicates_property_false_when_empty():
    result = find_duplicates(["UNIQUE=yes"])
    assert result.has_duplicates is False


def test_comment_lines_are_skipped():
    """Lines starting with '#' should be treated as comments and not parsed as keys."""
    lines = ["# FOO=comment", "FOO=real_value", "FOO=duplicate"]
    result = find_duplicates(lines)
    # The comment line must not be counted as a FOO entry
    assert len(result.duplicates) == 1
    assert result.duplicates[0].key == "FOO"
