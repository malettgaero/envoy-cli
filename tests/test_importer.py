"""Tests for envoy.importer."""
import pytest
from envoy.importer import import_env, ImportError, ImportResult


def test_import_json_basic():
    content = '{"HOST": "localhost", "PORT": "5432"}'
    result = import_env(content, fmt="json")
    assert result.source_format == "json"
    assert result.env["HOST"] == "localhost"
    assert result.env["PORT"] == "5432"
    assert result.imported_count == 2


def test_import_json_invalid_raises():
    with pytest.raises(ImportError, match="Invalid JSON"):
        import_env("{bad json", fmt="json")


def test_import_json_non_object_raises():
    with pytest.raises(ImportError, match="root must be an object"):
        import_env('["a", "b"]', fmt="json")


def test_import_shell_basic():
    content = "export HOST=localhost\nexport PORT=5432\n"
    result = import_env(content, fmt="shell")
    assert result.source_format == "shell"
    assert result.env["HOST"] == "localhost"
    assert result.imported_count == 2


def test_import_shell_without_export_keyword():
    content = "HOST=localhost\nPORT=5432\n"
    result = import_env(content, fmt="shell")
    assert result.env["HOST"] == "localhost"


def test_import_shell_strips_quotes():
    content = 'export SECRET="my_secret"\n'
    result = import_env(content, fmt="shell")
    assert result.env["SECRET"] == "my_secret"


def test_import_yaml_basic():
    content = "HOST: localhost\nPORT: '5432'\n"
    result = import_env(content, fmt="yaml")
    assert result.source_format == "yaml"
    assert result.env["HOST"] == "localhost"
    assert result.env["PORT"] == "5432"


def test_import_yaml_skips_comments_and_blanks():
    content = "# comment\n\nHOST: localhost\n"
    result = import_env(content, fmt="yaml")
    assert result.imported_count == 1
    assert result.skipped_lines == []


def test_import_yaml_skips_invalid_lines():
    content = "HOST: localhost\n- invalid_list_item\n"
    result = import_env(content, fmt="yaml")
    assert result.imported_count == 1
    assert len(result.skipped_lines) == 1


def test_auto_detect_json():
    content = '{"A": "1"}'
    result = import_env(content, fmt="auto")
    assert result.source_format == "json"


def test_auto_detect_shell():
    content = "export A=1\nexport B=2\n"
    result = import_env(content, fmt="auto")
    assert result.source_format == "shell"


def test_auto_detect_yaml_fallback():
    content = "A: 1\nB: 2\n"
    result = import_env(content, fmt="auto")
    assert result.source_format == "yaml"


def test_unsupported_format_raises():
    with pytest.raises(ImportError, match="Unsupported"):
        import_env("data", fmt="toml")


def test_summary_with_skipped():
    content = "HOST: localhost\n- bad\n"
    result = import_env(content, fmt="yaml")
    s = result.summary()
    assert "Imported" in s
    assert "skipped" in s


def test_success_flag_all_imported():
    result = import_env('{"X": "1"}', fmt="json")
    assert result.success is True
