"""CLI command for splitting a .env file into multiple files by prefix."""
from __future__ import annotations

import click

from envoy.parser import parse_env_file, write_env_file, ParseError
from envoy.splitter import split_env


@click.command("split")
@click.argument("env_file", type=click.Path(exists=True))
@click.option(
    "--prefix",
    "prefixes",
    multiple=True,
    metavar="PREFIX:OUTPUT",
    help="Prefix pattern mapped to output file, e.g. DB_:db.env",
)
@click.option(
    "--default",
    "default_file",
    default=None,
    metavar="FILE",
    help="File to write unmatched keys to (omit to discard them).",
)
@click.option(
    "--strip-prefix",
    is_flag=True,
    default=False,
    help="Remove the matched prefix from key names in output files.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Print what would be written without touching the filesystem.",
)
def split_cmd(
    env_file: str,
    prefixes: tuple,
    default_file: str | None,
    strip_prefix: bool,
    dry_run: bool,
) -> None:
    """Split ENV_FILE into multiple files grouped by key prefix.

    Each --prefix option takes the form PREFIX_PATTERN:OUTPUT_FILE.
    Example: --prefix '^DB_:db.env' --prefix '^REDIS_:redis.env'
    """
    try:
        env = parse_env_file(env_file)
    except ParseError as exc:
        raise click.ClickException(str(exc)) from exc

    prefix_map: dict[str, str] = {}
    for raw in prefixes:
        if ":" not in raw:
            raise click.ClickException(
                f"Invalid --prefix value {raw!r}. Expected FORMAT: PATTERN:OUTPUT"
            )
        pattern, _, output = raw.partition(":")
        prefix_map[pattern] = output

    result = split_env(
        env,
        prefix_map,
        source_file=env_file,
        default_file=default_file,
        strip_prefix=strip_prefix,
    )

    for target, keys in result.files.items():
        click.echo(f"  -> {target}: {len(keys)} key(s)")
        if not dry_run:
            write_env_file(target, keys)

    if result.unmatched:
        click.echo(f"  (unmatched: {', '.join(sorted(result.unmatched))})")

    click.echo(result.summary())
