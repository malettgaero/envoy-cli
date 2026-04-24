"""CLI command: inject keys from one .env file into another."""
from __future__ import annotations

import click

from envoy.injector import inject_env
from envoy.parser import parse_env_file, write_env_file


@click.command("inject")
@click.argument("base_file", type=click.Path(exists=True))
@click.argument("source_file", type=click.Path(exists=True))
@click.option(
    "--key",
    "keys",
    multiple=True,
    help="Specific key(s) to inject. Repeatable. Injects all if omitted.",
)
@click.option(
    "--no-overwrite",
    "no_overwrite",
    is_flag=True,
    default=False,
    help="Skip keys that already exist in the base file.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be injected without writing.",
)
@click.option(
    "--output",
    "-o",
    default=None,
    type=click.Path(),
    help="Write result to this file instead of modifying base file in-place.",
)
def inject_cmd(
    base_file: str,
    source_file: str,
    keys: tuple,
    no_overwrite: bool,
    dry_run: bool,
    output: str | None,
) -> None:
    """Inject variables from SOURCE_FILE into BASE_FILE."""
    base = parse_env_file(base_file)
    source = parse_env_file(source_file)

    result = inject_env(
        base=base,
        source=source,
        keys=list(keys) if keys else None,
        overwrite=not no_overwrite,
        source_label=source_file,
    )

    for entry in result.entries:
        status = "overwrite" if entry.overwritten else "new"
        click.echo(f"  [{status}] {entry.key}={entry.value}")

    click.echo(result.summary())

    if dry_run:
        click.echo("Dry run — no files written.")
        return

    dest = output or base_file
    write_env_file(dest, result.env)
    click.echo(f"Written to {dest}")
