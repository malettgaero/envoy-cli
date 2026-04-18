"""CLI command for importing env variables from external formats."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from envoy.importer import import_env, ImportError as EnvImportError
from envoy.parser import write_env_file


@click.command("import")
@click.argument("input_file", type=click.Path(exists=True))
@click.option("-o", "--output", default=None, help="Output .env file path")
@click.option(
    "--fmt",
    default="auto",
    type=click.Choice(["auto", "json", "yaml", "shell"], case_sensitive=False),
    help="Input format (default: auto-detect)",
)
@click.option("--dry-run", is_flag=True, help="Preview without writing")
@click.option("--verbose", is_flag=True, help="Show imported keys")
def import_cmd(
    input_file: str,
    output: str | None,
    fmt: str,
    dry_run: bool,
    verbose: bool,
) -> None:
    """Import env variables from JSON, YAML, or shell export format."""
    src = Path(input_file)
    content = src.read_text(encoding="utf-8")

    try:
        result = import_env(content, fmt=fmt)
    except EnvImportError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    click.echo(result.summary())

    if verbose:
        for key, value in sorted(result.env.items()):
            click.echo(f"  {key}={value}")

    if result.skipped_lines:
        click.echo(f"Skipped lines ({len(result.skipped_lines)}):")
        for line in result.skipped_lines:
            click.echo(f"  {line!r}")

    if dry_run:
        click.echo("Dry run — no file written.")
        return

    dest = Path(output) if output else src.with_suffix(".env")
    write_env_file(dest, result.env)
    click.echo(f"Written to {dest}")
