"""CLI command: envoy count — report key statistics for a .env file."""
from __future__ import annotations

import click

from envoy.parser import parse_env_file, ParseError
from envoy.counter import count_env


@click.command("count")
@click.argument("env_file", type=click.Path(exists=True))
@click.option(
    "--verbose", "-v", is_flag=True, default=False,
    help="Show individual key names per category.",
)
def count_cmd(env_file: str, verbose: bool) -> None:
    """Count and categorise keys in ENV_FILE."""
    try:
        env = parse_env_file(env_file)
    except ParseError as exc:
        raise click.ClickException(str(exc)) from exc

    result = count_env(env)

    click.echo(f"Total keys : {result.total}")
    for entry in result.entries:
        click.echo(f"  {entry.category:<10} {entry.count}")
        if verbose:
            for key in entry.keys:
                click.echo(f"    - {key}")

    if result.total == 0:
        click.echo("No keys found.")
