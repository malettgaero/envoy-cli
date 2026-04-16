"""Edge-case tests for envoy.splitter."""
from envoy.splitter import split_env


def test_case_insensitive_pattern_match():
    env = {"db_host": "localhost"}
    result = split_env(env, {"^DB_": "db.env"})
    # Regex match is case-insensitive, so lowercase key should match
    assert "db_host" in result.files.get("db.env", {})


def test_first_matching_pattern_wins():
    env = {"DB_HOST": "localhost"}
    result = split_env(
        env,
        {"^DB_": "db.env", "^DB_HOST": "host.env"},
    )
    # First pattern in dict iteration order wins
    assert "DB_HOST" in result.files["db.env"]
    assert "host.env" not in result.files


def test_all_keys_unmatched_no_default():
    env = {"FOO": "1", "BAR": "2"}
    result = split_env(env, {"^DB_": "db.env"})
    assert sorted(result.unmatched) == ["BAR", "FOO"]
    assert result.files == {}


def test_source_file_label_stored_in_entry():
    env = {"DB_HOST": "localhost"}
    result = split_env(env, {"^DB_": "db.env"}, source_file="prod.env")
    assert result.entries[0].source_file == "prod.env"


def test_strip_prefix_no_underscore_separator():
    env = {"DBHOST": "localhost"}
    result = split_env(env, {"^DB": "db.env"}, strip_prefix=True)
    # After stripping literal 'DB' the remaining key is 'HOST'
    assert "HOST" in result.files["db.env"]


def test_values_preserved_without_modification():
    env = {"APP_SECRET": "p@$$w0rd!="}
    result = split_env(env, {"^APP_": "app.env"})
    assert result.files["app.env"]["APP_SECRET"] == "p@$$w0rd!="
