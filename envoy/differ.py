"""Line-level diff renderer for .env files."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple
import difflib


@dataclass
class DiffLine:
    tag: str        # 'equal', 'insert', 'delete', 'replace'
    line_no_a: int | None
    line_no_b: int | None
    content: str

    def to_dict(self) -> dict:
        return {
            "tag": self.tag,
            "line_no_a": self.line_no_a,
            "line_no_b": self.line_no_b,
            "content": self.content,
        }


@dataclass
class DiffReport:
    lines: List[DiffLine] = field(default_factory=list)
    added: int = 0
    removed: int = 0

    @property
    def has_changes(self) -> bool:
        return self.added > 0 or self.removed > 0

    def summary(self) -> str:
        return f"+{self.added} -{self.removed} lines changed"


def diff_lines(a_text: str, b_text: str) -> DiffReport:
    """Produce a line-level diff between two .env file texts."""
    a_lines = a_text.splitlines(keepends=True)
    b_lines = b_text.splitlines(keepends=True)

    matcher = difflib.SequenceMatcher(None, a_lines, b_lines, autojunk=False)
    report = DiffReport()

    for opcode, a0, a1, b0, b1 in matcher.get_opcodes():
        if opcode == "equal":
            for i, (la, lb) in enumerate(zip(a_lines[a0:a1], b_lines[b0:b1])):
                report.lines.append(DiffLine("equal", a0 + i + 1, b0 + i + 1, la.rstrip("\n")))
        elif opcode == "insert":
            for i, lb in enumerate(b_lines[b0:b1]):
                report.lines.append(DiffLine("insert", None, b0 + i + 1, lb.rstrip("\n")))
                report.added += 1
        elif opcode == "delete":
            for i, la in enumerate(a_lines[a0:a1]):
                report.lines.append(DiffLine("delete", a0 + i + 1, None, la.rstrip("\n")))
                report.removed += 1
        elif opcode == "replace":
            for i, la in enumerate(a_lines[a0:a1]):
                report.lines.append(DiffLine("delete", a0 + i + 1, None, la.rstrip("\n")))
                report.removed += 1
            for i, lb in enumerate(b_lines[b0:b1]):
                report.lines.append(DiffLine("insert", None, b0 + i + 1, lb.rstrip("\n")))
                report.added += 1

    return report
