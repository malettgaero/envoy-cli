"""CLI command: rewrite — find-and-replace across .env values."""
from __future__ import annotations

import click

from envoy.parser import parse_env_file, write_env_file
from envoy.rewriter import rewrite_env


@click.command("rewrite")
@click.argument("env_file", type=click.Path(exists=True))
@click.argument("pattern")
@click.argument("replacement")
@click.option(
    "--keys", "-k",
    multiple=True,
    help="Restrict rewrites to these keys (repeatable).",
)
@click.option(
    "--regex", "-r",
    is_flag=True,
    default=False,
    help="Treat PATTERN as a regular expression.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would change without writing to disk.",
)
@click.option(
    "--quiet", "-q",
    is_flag=True,
    default=False,
    help="Suppress output; only set exit code.",
)
def rewrite_cmd(
    env_file: str,
    pattern: str,
    replacement: str,
    keys: tuple,
    regex: bool,
    dry_run: bool,
    quiet: bool,
) -> None:
    """Find PATTERN in .env values and replace with REPLACEMENT."""
    env = parse_env_file(env_file)
    result = rewrite_env(
        env,
        pattern=pattern,
        replacement=replacement,
        keys=list(keys) if keys else None,
        regex=regex,
    )

    if not quiet:
        if result.changed:
            click.echo(result.summary())
        else:
            click.echo("No values matched the pattern.")

    if result.changed and not dry_run:
        write_env_file(env_file, result.env)
        if not quiet:
            click.echo(f"\nWrote {env_file} ({result.changed_count} value(s) updated).")
    elif result.changed and dry_run:
        if not quiet:
            click.echo("\n[dry-run] No changes written.")
