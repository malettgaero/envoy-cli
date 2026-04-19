from datetime import date
import pytest
from envoy.expirer import check_expiry, ExpiryResult

REF = date(2024, 6, 15)


@pytest.fixture
def base_env():
    return {
        "CERT_EXPIRY": "2024-05-01",
        "TOKEN_EXPIRY": "2024-07-20",
        "RENEWAL_DATE": "2024-06-30",
        "API_KEY": "abc123",
        "BUILD_VERSION": "1.0.0",
    }


def test_check_expiry_returns_result(base_env):
    result = check_expiry(base_env, reference_date=REF)
    assert isinstance(result, ExpiryResult)


def test_non_date_keys_not_in_entries(base_env):
    result = check_expiry(base_env, reference_date=REF)
    keys = [e.key for e in result.entries]
    assert "API_KEY" not in keys
    assert "BUILD_VERSION" not in keys


def test_expired_key_detected(base_env):
    result = check_expiry(base_env, reference_date=REF)
    expired_keys = [e.key for e in result.expired]
    assert "CERT_EXPIRY" in expired_keys


def test_future_key_not_expired(base_env):
    result = check_expiry(base_env, reference_date=REF)
    expired_keys = [e.key for e in result.expired]
    assert "TOKEN_EXPIRY" not in expired_keys


def test_expiring_soon_within_30_days(base_env):
    result = check_expiry(base_env, reference_date=REF)
    soon_keys = [e.key for e in result.expiring_soon]
    assert "RENEWAL_DATE" in soon_keys


def test_days_remaining_positive_for_future(base_env):
    result = check_expiry(base_env, reference_date=REF)
    entry = next(e for e in result.entries if e.key == "TOKEN_EXPIRY")
    assert entry.days_remaining > 0


def test_days_remaining_negative_for_expired(base_env):
    result = check_expiry(base_env, reference_date=REF)
    entry = next(e for e in result.entries if e.key == "CERT_EXPIRY")
    assert entry.days_remaining < 0


def test_passed_false_when_expired(base_env):
    result = check_expiry(base_env, reference_date=REF)
    assert result.passed is False


def test_passed_true_when_no_expired():
    env = {"NEXT_RENEWAL": "2025-01-01"}
    result = check_expiry(env, reference_date=REF)
    assert result.passed is True


def test_filter_by_keys(base_env):
    result = check_expiry(base_env, keys=["CERT_EXPIRY"], reference_date=REF)
    assert len(result.entries) == 1
    assert result.entries[0].key == "CERT_EXPIRY"


def test_missing_key_in_filter_goes_to_skipped(base_env):
    result = check_expiry(base_env, keys=["MISSING_KEY"], reference_date=REF)
    assert "MISSING_KEY" in result.skipped


def test_summary_contains_checked_count(base_env):
    result = check_expiry(base_env, reference_date=REF)
    assert "checked" in result.summary()


def test_to_dict_on_entry(base_env):
    result = check_expiry(base_env, reference_date=REF)
    d = result.entries[0].to_dict()
    assert "key" in d and "parsed_date" in d and "expired" in d


def test_slash_date_format():
    env = {"EXPIRY": "01/01/2020"}
    result = check_expiry(env, reference_date=REF)
    assert len(result.entries) == 1
    assert result.entries[0].expired is True
