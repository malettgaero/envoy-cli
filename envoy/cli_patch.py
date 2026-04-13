"""CLI command: envoy patch — update specific keys in a .env file."""

from __future__ import annotations

from pathlib import Path
from typing import List

import click

from envoy.patcher import patch_env


@click.command("patch")
@click.argument("env_file", type=click.Path(exists=True, path_type=Path))
@click.argument("assignments", nargs=-1, required=True, metavar="KEY=VALUE ...")
@click.option(
    "--no-add",
    "add_missing",
    is_flag=True,
    default=True,
    flag_value=False,
    help="Do not add keys that are absent from the file.",
)
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Treat missing keys as errors.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would change without writing to disk.",
)
def patch_cmd(
    env_file: Path,
    assignments: List[str],
    add_missing: bool,
    strict: bool,
    dry_run: bool,
) -> None:
    """Patch KEY=VALUE pairs into ENV_FILE in-place."""
    patches: dict[str, str] = {}
    for assignment in assignments:
        if "=" not in assignment:
            raise click.BadParameter(
                f"'{assignment}' is not a valid KEY=VALUE assignment.",
                param_hint="assignments",
            )
        key, _, value = assignment.partition("=")
        patches[key.strip()] = value

    result = patch_env(
        env_file,
        patches,
        add_missing=add_missing,
        strict=strict,
        dry_run=dry_run,
    )

    if not result.success:
        for err in result.errors:
            click.echo(click.style(f"error: {err}", fg="red"), err=True)
        raise SystemExit(1)

    prefix = "[dry-run] " if dry_run else ""
    for key, val in result.updated.items():
        click.echo(click.style(f"{prefix}updated  {key}={val}", fg="yellow"))
    for key, val in result.added.items():
        click.echo(click.style(f"{prefix}added    {key}={val}", fg="green"))
    for key in result.skipped:
        click.echo(click.style(f"{prefix}skipped  {key}", fg="cyan"))

    click.echo(result.summary())
