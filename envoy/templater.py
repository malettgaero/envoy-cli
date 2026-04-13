"""Template rendering for .env files — fills placeholders from a context dict."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


@dataclass
class TemplateError(Exception):
    missing: List[str]

    def __str__(self) -> str:  # noqa: D105
        keys = ", ".join(self.missing)
        return f"Template placeholders not resolved: {keys}"


@dataclass
class RenderResult:
    rendered: Dict[str, str]
    resolved: List[str] = field(default_factory=list)
    unresolved: List[str] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        return len(self.unresolved) == 0


def render_env(
    template: Dict[str, str],
    context: Dict[str, str],
    *,
    strict: bool = False,
) -> RenderResult:
    """Replace ``{{ KEY }}`` placeholders in *template* values using *context*.

    Parameters
    ----------
    template:
        Parsed .env dict whose values may contain ``{{ PLACEHOLDER }}`` tokens.
    context:
        Mapping used to resolve placeholders.
    strict:
        When *True* raise :class:`TemplateError` if any placeholder remains
        unresolved after substitution.
    """
    rendered: Dict[str, str] = {}
    resolved_keys: List[str] = []
    unresolved_keys: List[str] = []

    for env_key, value in template.items():
        placeholders = _PLACEHOLDER_RE.findall(value)
        if not placeholders:
            rendered[env_key] = value
            continue

        def _replace(match: re.Match) -> str:  # noqa: ANN001
            name = match.group(1)
            return context.get(name, match.group(0))

        new_value = _PLACEHOLDER_RE.sub(_replace, value)
        rendered[env_key] = new_value

        remaining = _PLACEHOLDER_RE.findall(new_value)
        if remaining:
            unresolved_keys.extend(remaining)
        else:
            resolved_keys.extend(placeholders)

    unresolved_keys = list(dict.fromkeys(unresolved_keys))
    resolved_keys = list(dict.fromkeys(resolved_keys))

    result = RenderResult(
        rendered=rendered,
        resolved=resolved_keys,
        unresolved=unresolved_keys,
    )

    if strict and not result.is_complete:
        raise TemplateError(missing=unresolved_keys)

    return result
