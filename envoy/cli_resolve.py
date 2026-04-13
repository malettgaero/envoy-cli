"""CLI commands for the resolver feature."""

from __future__ import annotations

import click

from envoy.parser import parse_env_file
from envoy.resolver import resolve_envs


@click.command("resolve")
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option(
    "--strategy",
    type=click.Choice(["last-wins", "first-wins"], case_sensitive=False),
    default="last-wins",
    show_default=True,
    help="Which source takes priority when the same key appears in multiple files.",
)
@click.option(
    "--show-shadowed",
    is_flag=True,
    default=False,
    help="Print keys that were overridden by a higher-priority source.",
)
@click.option(
    "--quiet",
    is_flag=True,
    default=False,
    help="Only print the resolved KEY=VALUE pairs.",
)
def resolve_cmd(
    files: tuple[str, ...],
    strategy: str,
    show_shadowed: bool,
    quiet: bool,
) -> None:
    """Resolve variables from multiple .env FILES with priority ordering.

    Files listed later have higher priority by default (last-wins).
    Use --strategy=first-wins to invert this behaviour.
    """
    sources = []
    for path in files:
        try:
            env = parse_env_file(path)
            sources.append((path, env))
        except Exception as exc:  # noqa: BLE001
            raise click.ClickException(f"Failed to parse '{path}': {exc}") from exc

    last_wins = strategy.lower() == "last-wins"
    result = resolve_envs(sources, last_wins=last_wins)

    for key, entry in sorted(result.resolved.items()):
        click.echo(f"{key}={entry.value}")

    if not quiet:
        click.echo("")
        click.echo(result.summary())

    if show_shadowed and result.shadowed:
        click.echo("\nShadowed entries:")
        for entry in result.shadowed:
            click.echo(
                f"  {entry.key}: '{entry.value}' (from '{entry.source}') "
                f"-> overridden by '{entry.overridden_by}'"
            )
