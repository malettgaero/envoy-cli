"""Export parsed .env data to various formats (JSON, YAML, shell export statements)."""

from __future__ import annotations

import json
from enum import Enum
from typing import Dict


class ExportFormat(str, Enum):
    JSON = "json"
    YAML = "yaml"
    SHELL = "shell"


class ExportError(Exception):
    """Raised when an export operation fails."""


def export_env(env: Dict[str, str], fmt: ExportFormat) -> str:
    """Serialize *env* dict to the requested format string.

    Args:
        env:  Mapping of key -> value produced by the parser.
        fmt:  One of ExportFormat.JSON | YAML | SHELL.

    Returns:
        A formatted string ready to be written to stdout or a file.

    Raises:
        ExportError: If *fmt* is unsupported or a dependency is missing.
    """
    if fmt == ExportFormat.JSON:
        return _to_json(env)
    if fmt == ExportFormat.YAML:
        return _to_yaml(env)
    if fmt == ExportFormat.SHELL:
        return _to_shell(env)
    raise ExportError(f"Unsupported export format: {fmt!r}")


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _to_json(env: Dict[str, str]) -> str:
    return json.dumps(env, indent=2, sort_keys=True)


def _to_yaml(env: Dict[str, str]) -> str:
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise ExportError(
            "PyYAML is required for YAML export: pip install pyyaml"
        ) from exc
    return yaml.dump(env, default_flow_style=False, sort_keys=True).rstrip("\n")


def _to_shell(env: Dict[str, str]) -> str:
    lines = []
    for key in sorted(env):
        value = env[key].replace('"', '\\"')
        lines.append(f'export {key}="{value}"')
    return "\n".join(lines)
