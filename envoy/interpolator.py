"""Variable interpolation for .env files.

Supports ${VAR} and $VAR style references within values,
allowing one key to reference another defined in the same env.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List

_BRACE_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
_BARE_RE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")


@dataclass
class InterpolationWarning:
    key: str
    ref: str
    message: str

    def __str__(self) -> str:
        return f"{self.key}: {self.message} (ref: '{self.ref}')"


@dataclass
class InterpolateResult:
    env: Dict[str, str]
    warnings: List[InterpolationWarning] = field(default_factory=list)

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

    def summary(self) -> str:
        if not self.has_warnings:
            return "Interpolation complete — no unresolved references."
        lines = [f"Interpolation finished with {len(self.warnings)} warning(s):"]
        for w in self.warnings:
            lines.append(f"  - {w}")
        return "\n".join(lines)


def interpolate_env(
    env: Dict[str, str],
    *,
    strict: bool = False,
) -> InterpolateResult:
    """Resolve variable references inside env values.

    Parameters
    ----------
    env:
        Mapping of key -> raw value (may contain ``${VAR}`` or ``$VAR``).
    strict:
        If *True*, raise ``ValueError`` when a reference cannot be resolved.

    Returns
    -------
    InterpolateResult
        Resolved env dict plus any warnings about unresolved references.
    """
    resolved: Dict[str, str] = {}
    warnings: List[InterpolationWarning] = []

    for key, value in env.items():
        new_value, w = _resolve(key, value, env, strict=strict)
        resolved[key] = new_value
        warnings.extend(w)

    return InterpolateResult(env=resolved, warnings=warnings)


def has_references(value: str) -> bool:
    """Return *True* if *value* contains any ``${VAR}`` or ``$VAR`` references.

    Useful for quickly skipping interpolation on values that contain no
    variable placeholders.

    >>> has_references("hello world")
    False
    >>> has_references("hello $NAME")
    True
    >>> has_references("path=${BASE}/bin")
    True
    """
    return bool(_BRACE_RE.search(value) or _BARE_RE.search(value))


def _resolve(
    key: str,
    value: str,
    env: Dict[str, str],
    *,
    strict: bool,
) -> tuple[str, List[InterpolationWarning]]:
    warnings: List[InterpolationWarning] = []

    if not has_references(value):
        return value, warnings

    def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
        ref = match.group(1)
        if ref in env:
            return env[ref]
        msg = f"Unresolved reference '${{{ref}}}'"
        if strict:
            raise ValueError(f"{key}: {msg}")
        warnings.append(InterpolationWarning(key=key, ref=ref, message=msg))
        return match.group(0)  # leave original placeholder intact

    result = _BRACE_RE.sub(_replace, value)
    result = _BARE_RE.sub(_replace, result)
    return result, warnings
