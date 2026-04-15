"""CLI command for normalizing .env file keys and values."""
from __future__ import annotations

import click

from envoy.normalizer import normalize_env
from envoy.parser import parse_env_file, write_env_file


@click.command("normalize")
@click.argument("env_file", type=click.Path(exists=True))
@click.option("--no-uppercase", is_flag=True, default=False, help="Do not uppercase keys.")
@click.option("--no-strip", is_flag=True, default=False, help="Do not strip whitespace from values.")
@click.option(
    "--no-replace-spaces",
    is_flag=True,
    default=False,
    help="Do not replace spaces in keys.",
)
@click.option(
    "--space-char",
    default="_",
    show_default=True,
    help="Replacement character for spaces in keys.",
)
@click.option("--dry-run", is_flag=True, default=False, help="Preview changes without writing.")
@click.option("--quiet", is_flag=True, default=False, help="Suppress per-entry output.")
def normalize_cmd(
    env_file: str,
    no_uppercase: bool,
    no_strip: bool,
    no_replace_spaces: bool,
    space_char: str,
    dry_run: bool,
    quiet: bool,
) -> None:
    """Normalize keys and values in an .env file."""
    env = parse_env_file(env_file)
    result = normalize_env(
        env,
        uppercase_keys=not no_uppercase,
        strip_values=not no_strip,
        replace_spaces_in_keys=not no_replace_spaces,
        space_replacement=space_char,
    )

    if not quiet:
        for entry in result.entries:
            key_changed = entry.key != entry.original_key
            val_changed = entry.normalized_value != entry.original_value
            if key_changed:
                click.echo(f"  key:   {entry.original_key!r} -> {entry.key!r}")
            if val_changed:
                click.echo(f"  value: {entry.key}: {entry.original_value!r} -> {entry.normalized_value!r}")

    if not result.changed:
        click.echo("Nothing to normalize.")
        return

    if dry_run:
        click.echo(f"[dry-run] {result.summary()}")
        return

    write_env_file(env_file, result.env)
    click.echo(result.summary())
