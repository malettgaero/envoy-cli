from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re


@dataclass
class StrictViolation:
    key: str
    reason: str

    def to_dict(self) -> dict:
        return {"key": self.key, "reason": self.reason}

    def __str__(self) -> str:
        return f"{self.key}: {self.reason}"


@dataclass
class StrictResult:
    violations: List[StrictViolation] = field(default_factory=list)
    checked: int = 0

    def passed(self) -> bool:
        return len(self.violations) == 0

    def summary(self) -> str:
        if self.passed():
            return f"All {self.checked} keys passed strict mode checks."
        return f"{len(self.violations)} violation(s) found in {self.checked} keys."


_VALID_KEY_RE = re.compile(r'^[A-Z][A-Z0-9_]*$')
_NO_SPACES_RE = re.compile(r'\s')


def strict_check(
    env: Dict[str, str],
    require_uppercase: bool = True,
    disallow_empty: bool = True,
    max_value_length: Optional[int] = None,
    forbidden_patterns: Optional[List[str]] = None,
) -> StrictResult:
    violations: List[StrictViolation] = []
    forbidden_patterns = forbidden_patterns or []

    for key, value in env.items():
        if require_uppercase and not _VALID_KEY_RE.match(key):
            violations.append(StrictViolation(key, "Key must be uppercase with only letters, digits, and underscores"))

        if disallow_empty and value.strip() == "":
            violations.append(StrictViolation(key, "Value must not be empty or blank"))

        if max_value_length is not None and len(value) > max_value_length:
            violations.append(StrictViolation(key, f"Value exceeds max length of {max_value_length}"))

        for pattern in forbidden_patterns:
            if re.search(pattern, value):
                violations.append(StrictViolation(key, f"Value matches forbidden pattern: {pattern}"))
                break

    return StrictResult(violations=violations, checked=len(env))
