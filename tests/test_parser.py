"""Tests for envoy.parser module."""

import textwrap
from pathlib import Path

import pytest

from envoy.parser import parse_env_file, write_env_file, ParseError


@pytest.fixture()
def tmp_env(tmp_path):
    """Return a helper that writes a .env file and returns its path."""

    def _make(content: str) -> str:
        p = tmp_path / ".env"
        p.write_text(textwrap.dedent(content), encoding="utf-8")
        return str(p)

    return _make


def test_parse_simple_pairs(tmp_env):
    path = tmp_env("""
        KEY=value
        PORT=8080
    """)
    result = parse_env_file(path)
    assert result == {"KEY": "value", "PORT": "8080"}


def test_parse_skips_comments_and_blanks(tmp_env):
    path = tmp_env("""
        # This is a comment
        FOO=bar

        # another comment
        BAZ=qux
    """)
    result = parse_env_file(path)
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_parse_strips_double_quotes(tmp_env):
    path = tmp_env('SECRET="my secret value"\n')
    result = parse_env_file(path)
    assert result["SECRET"] == "my secret value"


def test_parse_strips_single_quotes(tmp_env):
    path = tmp_env("TOKEN='abc123'\n")
    result = parse_env_file(path)
    assert result["TOKEN"] == "abc123"


def test_parse_raises_for_invalid_line(tmp_env):
    path = tmp_env("INVALID LINE\n")
    with pytest.raises(ParseError) as exc_info:
        parse_env_file(path)
    assert "invalid syntax" in str(exc_info.value)


def test_parse_raises_file_not_found():
    with pytest.raises(FileNotFoundError):
        parse_env_file("/nonexistent/.env")


def test_write_and_reparse(tmp_path):
    data = {"APP_NAME": "envoy", "DEBUG": "false", "DB_URL": "postgres://localhost/db"}
    dest = str(tmp_path / ".env")
    write_env_file(dest, data)
    result = parse_env_file(dest)
    assert result == data
