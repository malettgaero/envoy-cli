"""CLI command for renaming keys inside a .env file."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from envoy.parser import parse_env_file, write_env_file, ParseError
from envoy.renamer import rename_keys


@click.command("rename")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("renames", nargs=-1, required=True, metavar="OLD=NEW...")
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite the destination key if it already exists.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Preview changes without writing to disk.",
)
@click.option(
    "--out",
    "output",
    default=None,
    type=click.Path(dir_okay=False),
    help="Write result to a different file instead of updating in place.",
)
def rename_cmd(
    env_file: str,
    renames: tuple,
    overwrite: bool,
    dry_run: bool,
    output: str | None,
) -> None:
    """Rename one or more keys in ENV_FILE.

    Provide each rename as OLD=NEW, e.g.:

        envoy rename .env DB_HOST=DATABASE_HOST APP_KEY=SECRET_KEY
    """
    rename_map: dict[str, str] = {}
    for token in renames:
        if "=" not in token:
            click.echo(f"[error] Invalid rename spec '{token}' — expected OLD=NEW", err=True)
            sys.exit(1)
        old, new = token.split("=", 1)
        rename_map[old.strip()] = new.strip()

    try:
        env = parse_env_file(Path(env_file))
    except ParseError as exc:
        click.echo(f"[error] {exc}", err=True)
        sys.exit(1)

    result = rename_keys(env, rename_map, overwrite=overwrite)

    click.echo(result.summary())

    if dry_run:
        click.echo("[dry-run] No changes written.")
        return

    dest = Path(output) if output else Path(env_file)
    write_env_file(dest, result.env)
    click.echo(f"Written to {dest}")
