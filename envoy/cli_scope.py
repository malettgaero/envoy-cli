"""CLI command: envoy scope — filter env keys by prefix scope."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click

from envoy.parser import parse_env_file, write_env_file, ParseError
from envoy.scoper import scope_env


@click.command("scope")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("prefixes", nargs=-1, required=True)
@click.option(
    "--strip-prefix",
    is_flag=True,
    default=False,
    help="Remove the matched prefix from output key names.",
)
@click.option(
    "--case-insensitive",
    is_flag=True,
    default=False,
    help="Match prefixes case-insensitively.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False),
    default=None,
    help="Write filtered env to this file instead of stdout.",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    default=False,
    help="Suppress summary output.",
)
def scope_cmd(
    env_file: str,
    prefixes: tuple,
    strip_prefix: bool,
    case_insensitive: bool,
    output: Optional[str],
    quiet: bool,
) -> None:
    """Filter ENV_FILE to keys whose names start with one of PREFIXES.

    Example:

        envoy scope .env DB_ APP_ --strip-prefix
    """
    try:
        env = parse_env_file(Path(env_file))
    except ParseError as exc:
        click.echo(f"Parse error: {exc}", err=True)
        sys.exit(1)

    result = scope_env(
        env,
        list(prefixes),
        strip_prefix=strip_prefix,
        case_sensitive=not case_insensitive,
    )

    if output:
        write_env_file(Path(output), result.env)
        if not quiet:
            click.echo(f"Written to {output}. {result.summary()}")
    else:
        for key, value in result.env.items():
            click.echo(f"{key}={value}")
        if not quiet:
            click.echo(f"\n# {result.summary()}")
