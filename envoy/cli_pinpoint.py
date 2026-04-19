"""CLI command: pinpoint — locate keys across multiple .env files."""
import click
from envoy.parser import parse_env_file
from envoy.pinpointer import pinpoint_env


@click.command("pinpoint")
@click.argument("keys", nargs=-1, required=True)
@click.option(
    "--file", "-f",
    "files",
    multiple=True,
    required=True,
    type=click.Path(exists=True),
    help=".env file to search (repeatable).",
)
@click.option("--show-values", is_flag=True, default=False, help="Print values alongside sources.")
@click.option("--inconsistent-only", is_flag=True, default=False, help="Only show keys with differing values.")
def pinpoint_cmd(keys, files, show_values, inconsistent_only):
    """Locate which .env file(s) define KEY(s)."""
    sources = {}
    for path in files:
        try:
            sources[path] = parse_env_file(path)
        except Exception as exc:
            raise click.ClickException(f"Cannot read {path}: {exc}")

    result = pinpoint_env(list(keys), sources)

    if not result.entries:
        click.echo("No matching keys found.")
        raise SystemExit(1)

    for entry in result.entries:
        if inconsistent_only and entry.is_consistent:
            continue
        status = "" if entry.is_consistent else " [INCONSISTENT]"
        click.echo(f"{entry.key}: found in {len(entry.sources)} file(s){status}")
        for src in entry.sources:
            val_part = f" = {entry.values[src]!r}" if show_values else ""
            click.echo(f"  {src}{val_part}")

    # Exit non-zero if any key is inconsistent
    if any(not e.is_consistent for e in result.entries):
        raise SystemExit(2)
