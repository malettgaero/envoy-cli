"""CLI command for detecting duplicate keys in a .env file."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from envoy.duplicator import find_duplicates


@click.command("duplicates")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Exit with code 1 when duplicates are found.",
)
def duplicates_cmd(env_file: str, strict: bool) -> None:
    """Detect duplicate keys in ENV_FILE."""
    raw_lines = Path(env_file).read_text(encoding="utf-8").splitlines()
    result = find_duplicates(raw_lines)

    if not result.has_duplicates:
        click.echo("No duplicate keys found.")
        return

    click.echo(f"Found {len(result.duplicates)} duplicate key(s) in {env_file}:")
    for entry in result.duplicates:
        lines_str = ", ".join(str(ln) for ln in entry.lines)
        click.echo(
            f"  {entry.key}  —  {entry.occurrences} occurrences  (lines {lines_str})"
        )

    if strict:
        sys.exit(1)
