"""Parser module for reading and validating .env files."""

import re
from pathlib import Path
from typing import Dict, Optional, Tuple


ENV_LINE_RE = re.compile(
    r'^(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.*)$'
)
COMMENT_RE = re.compile(r'^\s*#.*$')


class ParseError(Exception):
    """Raised when a .env file contains invalid syntax."""

    def __init__(self, path: str, line_no: int, line: str) -> None:
        self.path = path
        self.line_no = line_no
        self.line = line
        super().__init__(
            f"{path}:{line_no}: invalid syntax -> {line!r}"
        )


def parse_env_file(path: str) -> Dict[str, str]:
    """Parse a .env file and return a dict of key-value pairs.

    Args:
        path: Path to the .env file.

    Returns:
        Ordered dict of environment variable names to their values.

    Raises:
        FileNotFoundError: If the file does not exist.
        ParseError: If a non-comment, non-blank line cannot be parsed.
    """
    env_path = Path(path)
    if not env_path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    result: Dict[str, str] = {}

    with env_path.open(encoding="utf-8") as fh:
        for line_no, raw_line in enumerate(fh, start=1):
            line = raw_line.rstrip("\n")

            # Skip blank lines and comments
            if not line.strip() or COMMENT_RE.match(line):
                continue

            match = ENV_LINE_RE.match(line)
            if not match:
                raise ParseError(path, line_no, line)

            key = match.group("key")
            value = _strip_quotes(match.group("value").strip())
            result[key] = value

    return result


def _strip_quotes(value: str) -> str:
    """Remove surrounding single or double quotes from a value."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value


def write_env_file(path: str, data: Dict[str, str]) -> None:
    """Write a dict of key-value pairs to a .env file.

    Args:
        path: Destination file path.
        data: Mapping of environment variable names to values.
    """
    env_path = Path(path)
    with env_path.open("w", encoding="utf-8") as fh:
        for key, value in data.items():
            # Quote values that contain spaces or special characters
            if any(c in value for c in (' ', '#', '"', "'")):
                value = f'"{value}"'
            fh.write(f"{key}={value}\n")
