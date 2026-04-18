"""Score an env file for quality based on various heuristics."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ScoreEntry:
    key: str
    points: int
    deductions: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"key": self.key, "points": self.points, "deductions": self.deductions}


@dataclass
class ScoreResult:
    entries: List[ScoreEntry]
    max_score: int
    total_score: int

    @property
    def percent(self) -> float:
        if self.max_score == 0:
            return 100.0
        return round(self.total_score / self.max_score * 100, 1)

    @property
    def grade(self) -> str:
        p = self.percent
        if p >= 90:
            return "A"
        if p >= 75:
            return "B"
        if p >= 60:
            return "C"
        if p >= 40:
            return "D"
        return "F"

    def summary(self) -> str:
        return f"Score: {self.total_score}/{self.max_score} ({self.percent}%) Grade: {self.grade}"


_POINTS_PER_KEY = 10
_DEDUCTION_EMPTY_VALUE = 4
_DEDUCTION_LOWERCASE_KEY = 2
_DEDUCTION_NO_COMMENT = 1


def score_env(
    env: Dict[str, str],
    lines: List[str] | None = None,
    *,
    penalise_empty: bool = True,
    penalise_lowercase: bool = True,
    penalise_no_comment: bool = False,
) -> ScoreResult:
    """Score each key in *env* and return a ScoreResult."""
    comment_keys: set[str] = set()
    if lines and penalise_no_comment:
        prev_comment = False
        for raw in lines:
            stripped = raw.strip()
            if stripped.startswith("#"):
                prev_comment = True
            elif "=" in stripped and not stripped.startswith("#"):
                key = stripped.split("=", 1)[0].strip()
                if prev_comment:
                    comment_keys.add(key)
                prev_comment = False
            else:
                prev_comment = False

    entries: List[ScoreEntry] = []
    for key, value in env.items():
        pts = _POINTS_PER_KEY
        deductions: List[str] = []

        if penalise_empty and value == "":
            pts -= _DEDUCTION_EMPTY_VALUE
            deductions.append("empty value")
        if penalise_lowercase and key != key.upper():
            pts -= _DEDUCTION_LOWERCASE_KEY
            deductions.append("lowercase key")
        if penalise_no_comment and key not in comment_keys:
            pts -= _DEDUCTION_NO_COMMENT
            deductions.append("no preceding comment")

        entries.append(ScoreEntry(key=key, points=max(pts, 0), deductions=deductions))

    entries.sort(key=lambda e: e.key)
    max_score = len(entries) * _POINTS_PER_KEY
    total_score = sum(e.points for e in entries)
    return ScoreResult(entries=entries, max_score=max_score, total_score=total_score)
