"""CLI commands for env promotion between environment files."""
from __future__ import annotations

import click

from envoy.parser import parse_env_file, write_env_file
from envoy.promoter import promote_env


@click.group("promote")
def promote_cmd():
    """Promote keys from one .env file to another."""


@promote_cmd.command("apply")
@click.argument("source", type=click.Path(exists=True))
@click.argument("target", type=click.Path(exists=True))
@click.option(
    "--keys", "-k",
    multiple=True,
    help="Specific keys to promote (repeatable).  Defaults to all source keys.",
)
@click.option(
    "--no-overwrite",
    is_flag=True,
    default=False,
    help="Skip keys that already exist in the target file.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would change without writing to disk.",
)
def apply_cmd(source, target, keys, no_overwrite, dry_run):
    """Promote keys from SOURCE .env into TARGET .env."""
    src_env = parse_env_file(source)
    tgt_env = parse_env_file(target)

    result = promote_env(
        src_env,
        tgt_env,
        keys=list(keys) if keys else None,
        overwrite=not no_overwrite,
    )

    if result.promoted_count == 0:
        click.echo("Nothing to promote.")
        if result.skipped:
            click.echo(f"Skipped: {', '.join(result.skipped)}")
        return

    for entry in result.entries:
        tag = "[overwrite]" if entry.overwritten else "[new]"
        click.echo(f"  {tag} {entry.key} = {entry.source_value}")

    if result.skipped:
        click.echo(f"Skipped ({len(result.skipped)}): {', '.join(result.skipped)}")

    if dry_run:
        click.echo("Dry-run: no changes written.")
        return

    merged = {**tgt_env, **result.env()}
    write_env_file(target, merged)
    click.echo(f"\n{result.summary()} → written to {target}")
