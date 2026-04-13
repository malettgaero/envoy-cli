"""Patch (in-place update) specific keys in a .env file without rewriting the whole file."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envoy.parser import parse_env_file, write_env_file


@dataclass
class PatchResult:
    updated: Dict[str, str] = field(default_factory=dict)   # key -> new value
    added: Dict[str, str] = field(default_factory=dict)     # key -> value
    skipped: List[str] = field(default_factory=list)        # keys not found when strict
    errors: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return not self.errors

    def summary(self) -> str:
        parts = []
        if self.updated:
            parts.append(f"{len(self.updated)} updated")
        if self.added:
            parts.append(f"{len(self.added)} added")
        if self.skipped:
            parts.append(f"{len(self.skipped)} skipped")
        return ", ".join(parts) if parts else "no changes"


def patch_env(
    path: Path,
    patches: Dict[str, str],
    *,
    add_missing: bool = True,
    strict: bool = False,
    dry_run: bool = False,
) -> PatchResult:
    """Apply *patches* to the .env file at *path*.

    Parameters
    ----------
    path:         Target .env file.
    patches:      Mapping of key -> new value to apply.
    add_missing:  When True (default) keys absent from the file are appended.
    strict:       When True, missing keys are treated as errors.
    dry_run:      Parse and compute changes but do not write to disk.
    """
    result = PatchResult()

    try:
        env = parse_env_file(path)
    except Exception as exc:  # noqa: BLE001
        result.errors.append(f"Failed to parse {path}: {exc}")
        return result

    for key, value in patches.items():
        if key in env:
            if env[key] != value:
                result.updated[key] = value
            env[key] = value
        else:
            if strict:
                result.errors.append(f"Key '{key}' not found in {path}")
            elif add_missing:
                result.added[key] = value
                env[key] = value
            else:
                result.skipped.append(key)

    if result.errors:
        return result

    if not dry_run and (result.updated or result.added):
        try:
            write_env_file(path, env)
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"Failed to write {path}: {exc}")

    return result
