"""CLI command: envoy cascade — apply layered .env files left-to-right."""
from __future__ import annotations

import click

from envoy.parser import parse_env_file, write_env_file, ParseError
from envoy.cascader import cascade_envs


@click.command("cascade")
@click.argument("files", nargs=-1, required=True, metavar="FILE...")
@click.option(
    "--output", "-o",
    default=None,
    help="Write the cascaded result to this file instead of stdout.",
)
@click.option(
    "--show-shadowed",
    is_flag=True,
    default=False,
    help="Print keys that were overridden by a later layer.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Print result without writing to --output.",
)
def cascade_cmd(
    files: tuple,
    output: str | None,
    show_shadowed: bool,
    dry_run: bool,
) -> None:
    """Cascade FILE... left-to-right; later files override earlier ones."""
    sources = []
    for path in files:
        try:
            env = parse_env_file(path)
            sources.append((path, env))
        except (ParseError, FileNotFoundError) as exc:
            raise click.ClickException(str(exc)) from exc

    result = cascade_envs(sources)

    click.echo(result.summary())

    if show_shadowed and result.shadowed:
        click.echo("\nShadowed keys:")
        for entry in result.shadowed:
            click.echo(
                f"  {entry.key}: '{entry.value}' ({entry.source})"
                f" → overridden by {entry.overridden_by}"
            )

    if output and not dry_run:
        write_env_file(output, result.env)
        click.echo(f"\nWrote cascaded env to {output}")
    elif output and dry_run:
        click.echo("\n[dry-run] would write:")
        for k, v in sorted(result.env.items()):
            click.echo(f"  {k}={v}")
    else:
        click.echo("\nResult:")
        for k, v in sorted(result.env.items()):
            click.echo(f"  {k}={v}")
