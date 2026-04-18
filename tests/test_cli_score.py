"""CLI tests for the score command."""
import pytest
from click.testing import CliRunner
from envoy.cli_score import score_cmd


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def tmp_env(tmp_path):
    def _make(content: str):
        p = tmp_path / ".env"
        p.write_text(content)
        return str(p)
    return _make


def test_score_clean_file_exits_zero(runner, tmp_env):
    path = tmp_env("HOST=localhost\nPORT=8080\n")
    result = runner.invoke(score_cmd, [path])
    assert result.exit_code == 0
    assert "Score:" in result.output
    assert "Grade:" in result.output


def test_score_verbose_shows_per_key(runner, tmp_env):
    path = tmp_env("HOST=localhost\n")
    result = runner.invoke(score_cmd, [path, "--verbose"])
    assert result.exit_code == 0
    assert "HOST" in result.output


def test_score_empty_value_deducted(runner, tmp_env):
    path = tmp_env("API_KEY=\n")
    result = runner.invoke(score_cmd, [path, "--verbose"])
    assert "empty value" in result.output


def test_score_lowercase_key_deducted(runner, tmp_env):
    path = tmp_env("db_host=localhost\n")
    result = runner.invoke(score_cmd, [path, "--verbose"])
    assert "lowercase key" in result.output


def test_score_no_penalise_empty_flag(runner, tmp_env):
    path = tmp_env("API_KEY=\n")
    result = runner.invoke(score_cmd, [path, "--verbose", "--no-penalise-empty"])
    assert "empty value" not in result.output


def test_score_grade_f_exits_nonzero(runner, tmp_env):
    # all lowercase + empty => low score
    content = "\n".join(f"key{i}=" for i in range(10)) + "\n"
    path = tmp_env(content)
    result = runner.invoke(score_cmd, [path])
    assert result.exit_code != 0


def test_score_penalise_no_comment(runner, tmp_env):
    path = tmp_env("HOST=localhost\n")
    result = runner.invoke(score_cmd, [path, "--verbose", "--penalise-no-comment"])
    assert "no preceding comment" in result.output


def test_score_comment_before_key_no_penalty(runner, tmp_env):
    path = tmp_env("# the host\nHOST=localhost\n")
    result = runner.invoke(score_cmd, [path, "--verbose", "--penalise-no-comment"])
    assert "no preceding comment" not in result.output
