"""Profile comparison: compare an env file against a named profile (e.g. 'production', 'staging')."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


PROFILE_REGISTRY: Dict[str, Dict[str, str]] = {}


@dataclass
class ProfileViolation:
    key: str
    expected: Optional[str]
    actual: Optional[str]
    reason: str

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "expected": self.expected,
            "actual": self.actual,
            "reason": self.reason,
        }


@dataclass
class ProfileResult:
    profile: str
    violations: List[ProfileViolation] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.violations) == 0

    def summary(self) -> str:
        if self.passed:
            return f"Profile '{self.profile}': all checks passed."
        lines = [f"Profile '{self.profile}': {len(self.violations)} violation(s)"]
        for v in self.violations:
            lines.append(f"  [{v.key}] {v.reason} (expected={v.expected!r}, actual={v.actual!r})")
        return "\n".join(lines)


def compare_profile(
    env: Dict[str, str],
    profile: Dict[str, str],
    profile_name: str = "custom",
    strict: bool = False,
) -> ProfileResult:
    """Compare *env* against *profile* key/value expectations.

    Each key in *profile* whose value is ``"*"`` means the key must be present
    with any non-empty value.  Any other value is matched literally.  When
    *strict* is True, keys present in *env* but absent from *profile* are also
    flagged.
    """
    violations: List[ProfileViolation] = []

    for key, expected in profile.items():
        actual = env.get(key)
        if actual is None:
            violations.append(
                ProfileViolation(key, expected, None, "key missing from env")
            )
        elif expected == "*":
            if actual.strip() == "":
                violations.append(
                    ProfileViolation(key, expected, actual, "key present but value is empty")
                )
        elif actual != expected:
            violations.append(
                ProfileViolation(key, expected, actual, "value mismatch")
            )

    if strict:
        for key in env:
            if key not in profile:
                violations.append(
                    ProfileViolation(key, None, env[key], "unexpected key not in profile")
                )

    return ProfileResult(profile=profile_name, violations=violations)
