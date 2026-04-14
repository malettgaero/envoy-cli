"""CLI command: envoy group — display env keys organised by prefix."""
from __future__ import annotations

import click

from envoy.grouper import group_env
from envoy.parser import parse_env_file


@click.command("group")
@click.argument("env_file", type=click.Path(exists=True))
@click.option(
    "--prefix",
    "prefixes",
    multiple=True,
    help="Explicit prefix(es) to group by (repeatable). Auto-detects if omitted.",
)
@click.option(
    "--no-auto",
    is_flag=True,
    default=False,
    help="Disable automatic prefix detection.",
)
@click.option(
    "--show-values",
    is_flag=True,
    default=False,
    help="Print values alongside keys (masked by default).",
)
def group_cmd(env_file: str, prefixes: tuple, no_auto: bool, show_values: bool) -> None:
    """Display env keys grouped by their prefix."""
    env = parse_env_file(env_file)
    explicit = list(prefixes) if prefixes else None
    result = group_env(env, prefixes=explicit, auto_detect=not no_auto)

    if not result.entries:
        click.echo("No keys found.")
        return

    for prefix, entries in result.groups.items():
        label = prefix if prefix else "(ungrouped)"
        click.echo(f"\n[{label}]")
        for entry in entries:
            if show_values:
                click.echo(f"  {entry.key}={entry.value}")
            else:
                click.echo(f"  {entry.key}")

    click.echo(f"\n{result.summary()}")
