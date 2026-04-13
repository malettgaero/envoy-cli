"""Validation logic for .env files against a schema/template."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class ValidationResult:
    missing_keys: List[str] = field(default_factory=list)
    extra_keys: List[str] = field(default_factory=list)
    empty_keys: List[str] = field(default_factory=list)
    invalid_keys: List[str] = field(default_factory=list)  # bad key names

    @property
    def is_valid(self) -> bool:
        return not (
            self.missing_keys
            or self.empty_keys
            or self.invalid_keys
        )

    def summary(self) -> str:
        lines: List[str] = []
        if self.missing_keys:
            lines.append("Missing keys:")
            for k in sorted(self.missing_keys):
                lines.append(f"  - {k}")
        if self.empty_keys:
            lines.append("Empty values:")
            for k in sorted(self.empty_keys):
                lines.append(f"  - {k}")
        if self.extra_keys:
            lines.append("Extra keys (not in template):")
            for k in sorted(self.extra_keys):
                lines.append(f"  ~ {k}")
        if self.invalid_keys:
            lines.append("Invalid key names:")
            for k in sorted(self.invalid_keys):
                lines.append(f"  ! {k}")
        if not lines:
            return "All checks passed."
        return "\n".join(lines)


IMPORT_KEY_RE = __import__("re").compile(r"^[A-Z_][A-Z0-9_]*$")


def validate_env(
    env: Dict[str, str],
    template: Optional[Dict[str, str]] = None,
    *,
    allow_empty: bool = False,
    strict: bool = False,
) -> ValidationResult:
    """Validate *env* against an optional *template*.

    Args:
        env: Parsed environment mapping.
        template: Reference mapping (e.g. .env.example). Keys present in the
            template are considered required.
        allow_empty: When False, keys with empty string values are flagged.
        strict: When True, keys present in *env* but absent from *template* are
            flagged as extra keys.
    """
    result = ValidationResult()

    # Key-name validation
    for key in env:
        if not IMPORT_KEY_RE.match(key):
            result.invalid_keys.append(key)

    # Empty-value check
    if not allow_empty:
        for key, value in env.items():
            if value == "":
                result.empty_keys.append(key)

    if template is not None:
        template_keys: Set[str] = set(template.keys())
        env_keys: Set[str] = set(env.keys())

        result.missing_keys = sorted(template_keys - env_keys)
        if strict:
            result.extra_keys = sorted(env_keys - template_keys)

    return result
