"""formatter.py — Normalize .env file formatting (quoting style, spacing around =)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FormatEntry:
    key: str
    original_line: str
    formatted_line: str
    changed: bool

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "original_line": self.original_line,
            "formatted_line": self.formatted_line,
            "changed": self.changed,
        }


@dataclass
class FormatResult:
    entries: List[FormatEntry] = field(default_factory=list)
    preserved_lines: List[str] = field(default_factory=list)  # comments / blanks

    @property
    def changed(self) -> bool:
        return any(e.changed for e in self.entries)

    @property
    def changed_count(self) -> int:
        return sum(1 for e in self.entries if e.changed)

    @property
    def env(self) -> Dict[str, str]:
        return {e.key: _value_from_line(e.formatted_line) for e in self.entries}

    def summary(self) -> str:
        if not self.changed:
            return "No formatting changes needed."
        return f"{self.changed_count} line(s) reformatted."


def _value_from_line(line: str) -> str:
    """Extract the raw value from a formatted KEY=VALUE line."""
    _, _, val = line.partition("=")
    return val


def _format_line(
    key: str,
    value: str,
    quote_values: bool,
    space_around_equals: bool,
) -> str:
    """Produce a canonical formatted line for a key/value pair."""
    if quote_values and " " in value and not (value.startswith('"') and value.endswith('"')):
        value = f'"{value}"'
    sep = " = " if space_around_equals else "="
    return f"{key}{sep}{value}"


def format_env(
    lines: List[str],
    *,
    quote_values: bool = False,
    space_around_equals: bool = False,
    uppercase_keys: bool = False,
) -> FormatResult:
    """Format each key=value line in *lines* according to the given style options."""
    result = FormatResult()

    for raw in lines:
        stripped = raw.rstrip("\n")

        # Preserve comments and blank lines as-is
        if stripped.lstrip().startswith("#") or stripped.strip() == "":
            result.preserved_lines.append(stripped)
            continue

        if "=" not in stripped:
            result.preserved_lines.append(stripped)
            continue

        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip()

        if uppercase_keys:
            key = key.upper()

        formatted = _format_line(key, value, quote_values, space_around_equals)
        result.entries.append(
            FormatEntry(
                key=key,
                original_line=stripped,
                formatted_line=formatted,
                changed=(formatted != stripped),
            )
        )

    return result
