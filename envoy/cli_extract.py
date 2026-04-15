"""CLI command: envoy extract — pull a subset of keys from an env file."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List

import click

from envoy.extractor import extract_env
from envoy.parser import parse_env_file, write_env_file


@click.command("extract")
@click.argument("src", type=click.Path(exists=True, dir_okay=False))
@click.option("-k", "--key", "keys", multiple=True, help="Exact key to extract.")
@click.option("-p", "--pattern", "patterns", multiple=True, help="Glob pattern to match keys.")
@click.option("-o", "--output", "output", default=None, help="Write extracted env to this file.")
@click.option("--dry-run", is_flag=True, default=False, help="Print result without writing.")
@click.option("--show-excluded", is_flag=True, default=False, help="Also list excluded keys.")
def extract_cmd(
    src: str,
    keys: List[str],
    patterns: List[str],
    output: str,
    dry_run: bool,
    show_excluded: bool,
) -> None:
    """Extract a subset of keys from SRC into a new env file."""
    env = parse_env_file(Path(src))
    result = extract_env(env, keys=list(keys), patterns=list(patterns))

    click.echo(result.summary())

    for entry in result.entries:
        click.echo(f"  + {entry.key}={entry.value}  (matched: {entry.matched_by})")

    if show_excluded:
        for k in result.excluded_keys:
            click.echo(f"  - {k}")

    if result.extracted_count == 0:
        click.echo("No keys matched — nothing to write.", err=True)
        sys.exit(1)

    if output and not dry_run:
        dest = Path(output)
        write_env_file(dest, result.env)
        click.echo(f"Written to {dest}")
    elif dry_run:
        click.echo("(dry-run) no file written.")
