"""CLI command: prune — remove keys from a .env file by name or glob pattern."""
from __future__ import annotations

import click

from envoy.parser import parse_env_file, write_env_file
from envoy.pruner import prune_env


@click.command("prune")
@click.argument("env_file", type=click.Path(exists=True))
@click.option(
    "-k", "--key",
    multiple=True,
    metavar="KEY",
    help="Exact key name to remove (repeatable).",
)
@click.option(
    "-p", "--pattern",
    multiple=True,
    metavar="PATTERN",
    help="Glob pattern to match keys for removal (repeatable).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be removed without writing changes.",
)
@click.option(
    "--quiet",
    is_flag=True,
    default=False,
    help="Suppress output; only set exit code.",
)
def prune_cmd(
    env_file: str,
    key: tuple,
    pattern: tuple,
    dry_run: bool,
    quiet: bool,
) -> None:
    """Remove keys from ENV_FILE that match KEY names or glob PATTERNs."""
    if not key and not pattern:
        raise click.UsageError(
            "Provide at least one --key or --pattern to prune."
        )

    env = parse_env_file(env_file)
    result = prune_env(env, keys=list(key), patterns=list(pattern))

    if not quiet:
        click.echo(result.summary())

    if result.changed and not dry_run:
        write_env_file(env_file, result.kept)
        if not quiet:
            click.echo(f"Written: {env_file}")
    elif dry_run and result.changed and not quiet:
        click.echo("(dry-run) No changes written.")
