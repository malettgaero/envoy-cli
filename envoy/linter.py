"""Linter for .env files — checks style and convention issues."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class LintIssue:
    line: int
    key: str
    code: str
    message: str

    def to_dict(self) -> dict:
        return {
            "line": self.line,
            "key": self.key,
            "code": self.code,
            "message": self.message,
        }


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.issues) == 0

    def summary(self) -> str:
        if self.passed:
            return "No lint issues found."
        lines = [f"{len(self.issues)} lint issue(s) found:"]
        for issue in self.issues:
            lines.append(
                f"  Line {issue.line} [{issue.code}] {issue.key!r}: {issue.message}"
            )
        return "\n".join(lines)


def lint_env(raw_lines: List[str]) -> LintResult:
    """Lint raw lines from a .env file and return a LintResult."""
    issues: List[LintIssue] = []

    for lineno, raw in enumerate(raw_lines, start=1):
        line = raw.rstrip("\n")

        # Skip blank lines and comments
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if "=" not in line:
            continue

        key, _, value = line.partition("=")

        # W001: key should be UPPER_SNAKE_CASE
        if key != key.upper():
            issues.append(
                LintIssue(lineno, key, "W001", "Key should be uppercase")
            )

        # W002: no spaces around the '='
        if key != key.rstrip() or value != value.lstrip():
            issues.append(
                LintIssue(lineno, key.strip(), "W002",
                          "Unexpected whitespace around '='")
            )

        # W003: value should not use single quotes (prefer double quotes)
        val_stripped = value.strip()
        if val_stripped.startswith("'") and val_stripped.endswith("'") and len(val_stripped) >= 2:
            issues.append(
                LintIssue(lineno, key.strip(), "W003",
                          "Prefer double quotes over single quotes")
            )

        # W004: trailing whitespace in value (unquoted)
        if not (val_stripped.startswith('"') and val_stripped.endswith('"')):
            if value != value.rstrip():
                issues.append(
                    LintIssue(lineno, key.strip(), "W004",
                              "Trailing whitespace in value")
                )

    return LintResult(issues=issues)
