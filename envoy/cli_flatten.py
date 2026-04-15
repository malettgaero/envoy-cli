"""CLI command for flattening dot-notation keys in a .env file."""
from __future__ import annotations

import click

from envoy.flattener import flatten_env, unflatten_env
from envoy.parser import parse_env_file, write_env_file


@click.group("flatten")
def flatten_cmd() -> None:
    """Flatten or unflatten dot-notation keys in a .env file."""


@flatten_cmd.command("apply")
@click.argument("env_file", type=click.Path(exists=True))
@click.option("--separator", default="__", show_default=True, help="Flat key separator.")
@click.option("--source-sep", default=".", show_default=True, help="Separator in source keys.")
@click.option("--dry-run", is_flag=True, help="Preview changes without writing.")
@click.option("--quiet", is_flag=True, help="Suppress summary output.")
def apply_cmd(
    env_file: str,
    separator: str,
    source_sep: str,
    dry_run: bool,
    quiet: bool,
) -> None:
    """Flatten dot-notation keys and write back to ENV_FILE."""
    env = parse_env_file(env_file)
    result = flatten_env(env, separator=separator, source_sep=source_sep)

    if not quiet:
        for entry in result.changed:
            click.echo(f"  {entry.original_key}  ->  {entry.flat_key}")
        click.echo(result.summary())

    if not dry_run:
        write_env_file(env_file, result.env)
        if not quiet:
            click.echo(f"Written: {env_file}")


@flatten_cmd.command("undo")
@click.argument("env_file", type=click.Path(exists=True))
@click.option("--separator", default="__", show_default=True, help="Flat key separator.")
@click.option("--target-sep", default=".", show_default=True, help="Separator to restore.")
@click.option("--dry-run", is_flag=True, help="Preview changes without writing.")
@click.option("--quiet", is_flag=True, help="Suppress output.")
def undo_cmd(
    env_file: str,
    separator: str,
    target_sep: str,
    dry_run: bool,
    quiet: bool,
) -> None:
    """Reverse a previous flatten operation (unflatten) on ENV_FILE."""
    env = parse_env_file(env_file)
    restored = unflatten_env(env, separator=separator, target_sep=target_sep)

    changed = [
        (k, restored[k])
        for k, v in env.items()
        if k != restored.get(k.replace(separator, target_sep), k)
    ]

    if not quiet:
        for orig, new_key in [
            (k, k.replace(separator, target_sep)) for k in env if separator in k
        ]:
            click.echo(f"  {orig}  ->  {new_key}")
        click.echo(f"{len([k for k in env if separator in k])} key(s) unflattened.")

    if not dry_run:
        write_env_file(env_file, restored)
        if not quiet:
            click.echo(f"Written: {env_file}")
