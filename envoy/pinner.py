"""envoy.pinner – Pin specific env keys to exact values and detect drift."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PinViolation:
    key: str
    pinned: str
    actual: Optional[str]  # None means key is absent

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "pinned": self.pinned,
            "actual": self.actual,
        }

    def __str__(self) -> str:
        if self.actual is None:
            return f"{self.key}: pinned to {self.pinned!r} but key is missing"
        return f"{self.key}: pinned to {self.pinned!r} but got {self.actual!r}"


@dataclass
class PinResult:
    violations: List[PinViolation] = field(default_factory=list)
    checked: int = 0

    @property
    def passed(self) -> bool:
        return len(self.violations) == 0

    def summary(self) -> str:
        if self.passed:
            return f"All {self.checked} pinned key(s) match."
        lines = [f"{len(self.violations)} pin violation(s) found:"]
        for v in self.violations:
            lines.append(f"  - {v}")
        return "\n".join(lines)


def pin_env(
    env: Dict[str, str],
    pins: Dict[str, str],
) -> PinResult:
    """Check that every key in *pins* exists in *env* with the exact pinned value.

    Args:
        env:  The resolved environment dictionary.
        pins: Mapping of key -> expected-value to enforce.

    Returns:
        A :class:`PinResult` describing any violations.
    """
    violations: List[PinViolation] = []

    for key, expected in pins.items():
        actual = env.get(key)  # None when absent
        if actual != expected:
            violations.append(PinViolation(key=key, pinned=expected, actual=actual))

    return PinResult(violations=violations, checked=len(pins))
