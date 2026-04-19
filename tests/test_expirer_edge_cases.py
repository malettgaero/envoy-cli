from datetime import date
from envoy.expirer import check_expiry, _parse_date


def test_empty_env_returns_empty_result():
    result = check_expiry({}, reference_date=date(2024, 1, 1))
    assert result.entries == []
    assert result.skipped == []


def test_invalid_date_string_skipped_without_filter():
    env = {"EXPIRY": "not-a-date"}
    result = check_expiry(env, reference_date=date(2024, 1, 1))
    assert result.entries == []


def test_exactly_today_is_not_expired():
    today = date(2024, 6, 15)
    env = {"EXPIRY": today.isoformat()}
    result = check_expiry(env, reference_date=today)
    assert result.entries[0].expired is False
    assert result.entries[0].days_remaining == 0


def test_exactly_today_is_in_expiring_soon():
    today = date(2024, 6, 15)
    env = {"EXPIRY": today.isoformat()}
    result = check_expiry(env, reference_date=today)
    assert result.entries[0] in result.expiring_soon


def test_parse_date_invalid_returns_none():
    assert _parse_date("hello") is None
    assert _parse_date("2024-13-01") is None
    assert _parse_date("") is None


def test_entries_sorted_alphabetically():
    env = {"Z_DATE": "2025-01-01", "A_DATE": "2025-06-01"}
    result = check_expiry(env, reference_date=date(2024, 1, 1))
    keys = [e.key for e in result.entries]
    assert keys == sorted(keys)
