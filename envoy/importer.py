"""Import env variables from external formats (JSON, YAML, shell export)."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Dict, List


class ImportError(Exception):
    pass


@dataclass
class ImportResult:
    env: Dict[str, str]
    imported_count: int
    skipped_lines: List[str] = field(default_factory=list)
    source_format: str = "unknown"

    @property
    def success(self) -> bool:
        return self.imported_count > 0 or not self.skipped_lines

    def summary(self) -> str:
        parts = [f"Imported {self.imported_count} key(s) from {self.source_format}"]
        if self.skipped_lines:
            parts.append(f"{len(self.skipped_lines)} line(s) skipped")
        return "; ".join(parts)


def import_env(content: str, fmt: str = "auto") -> ImportResult:
    fmt = fmt.lower()
    if fmt == "auto":
        fmt = _detect_format(content)
    if fmt == "json":
        return _from_json(content)
    if fmt in ("yaml", "yml"):
        return _from_yaml(content)
    if fmt in ("shell", "sh"):
        return _from_shell(content)
    raise ImportError(f"Unsupported import format: {fmt}")


def _detect_format(content: str) -> str:
    stripped = content.strip()
    if stripped.startswith("{"):
        return "json"
    if re.search(r"^export\s+\w+=", content, re.MULTILINE):
        return "shell"
    return "yaml"


def _from_json(content: str) -> ImportResult:
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ImportError(f"Invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ImportError("JSON root must be an object")
    env = {str(k): str(v) for k, v in data.items()}
    return ImportResult(env=env, imported_count=len(env), source_format="json")


def _from_yaml(content: str) -> ImportResult:
    env: Dict[str, str] = {}
    skipped: List[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        m = re.match(r'^([\w.\-]+):\s*(.*)$', stripped)
        if m:
            env[m.group(1)] = m.group(2).strip('"\'')
        else:
            skipped.append(line)
    return ImportResult(env=env, imported_count=len(env), skipped_lines=skipped, source_format="yaml")


def _from_shell(content: str) -> ImportResult:
    env: Dict[str, str] = {}
    skipped: List[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        m = re.match(r'^(?:export\s+)?(\w+)=(.*)$', stripped)
        if m:
            env[m.group(1)] = m.group(2).strip('"\'')
        else:
            skipped.append(line)
    return ImportResult(env=env, imported_count=len(env), skipped_lines=skipped, source_format="shell")
