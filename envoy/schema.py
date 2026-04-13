"""Schema validation for .env files against a declared spec."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re


@dataclass
class SchemaField:
    key: str
    required: bool = True
    pattern: Optional[str] = None
    allowed_values: Optional[List[str]] = None
    description: str = ""


@dataclass
class SchemaViolation:
    key: str
    reason: str

    def __str__(self) -> str:
        return f"{self.key}: {self.reason}"


@dataclass
class SchemaResult:
    violations: List[SchemaViolation] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.violations) == 0

    def summary(self) -> str:
        if self.is_valid:
            return "Schema validation passed."
        lines = [f"Schema validation failed ({len(self.violations)} issue(s)):"]
        for v in self.violations:
            lines.append(f"  - {v}")
        return "\n".join(lines)


def validate_schema(
    env: Dict[str, str],
    schema: List[SchemaField],
) -> SchemaResult:
    """Validate *env* against the declared *schema* fields."""
    result = SchemaResult()

    for field_def in schema:
        key = field_def.key
        value = env.get(key)

        if value is None:
            if field_def.required:
                result.violations.append(
                    SchemaViolation(key, "required key is missing")
                )
            continue

        if field_def.allowed_values is not None and value not in field_def.allowed_values:
            allowed = ", ".join(field_def.allowed_values)
            result.violations.append(
                SchemaViolation(key, f"value {value!r} not in allowed values [{allowed}]")
            )

        if field_def.pattern is not None and not re.fullmatch(field_def.pattern, value):
            result.violations.append(
                SchemaViolation(key, f"value {value!r} does not match pattern {field_def.pattern!r}")
            )

    return result


def load_schema_from_dict(raw: Dict) -> List[SchemaField]:
    """Build a list of SchemaField objects from a plain dictionary (e.g. parsed JSON/YAML)."""
    fields: List[SchemaField] = []
    for key, spec in raw.items():
        fields.append(
            SchemaField(
                key=key,
                required=spec.get("required", True),
                pattern=spec.get("pattern"),
                allowed_values=spec.get("allowed_values"),
                description=spec.get("description", ""),
            )
        )
    return fields
