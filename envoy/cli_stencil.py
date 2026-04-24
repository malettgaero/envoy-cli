"""CLI command: stencil – filter an env file through a key whitelist."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from envoy.parser import parse_env_file, write_env_file
from envoy.stenciler import apply_stencil


@click.command("stencil")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--key",
    "keys",
    multiple=True,
    required=True,
    help="Key to include in the stencil (repeat for multiple keys).",
)
@click.option(
    "--output", "-o",
    default=None,
    help="Write filtered env to this file instead of stdout.",
)
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Exit non-zero if any stencil key is missing from the source file.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be written without actually writing.",
)
def stencil_cmd(
    env_file: str,
    keys: tuple,
    output: str | None,
    strict: bool,
    dry_run: bool,
) -> None:
    """Filter ENV_FILE to only the keys listed via --key."""
    source = parse_env_file(Path(env_file))
    result = apply_stencil(source, list(keys))

    click.echo(result.summary())

    if result.missing_keys:
        click.echo("Missing keys: " + ", ".join(result.missing_keys), err=True)

    if result.dropped_keys:
        click.echo("Dropped keys: " + ", ".join(result.dropped_keys))

    if not dry_run:
        if output:
            write_env_file(Path(output), result.env)
            click.echo(f"Written to {output}")
        else:
            for k, v in result.env.items():
                click.echo(f"{k}={v}")

    if strict and not result.passed:
        sys.exit(1)
