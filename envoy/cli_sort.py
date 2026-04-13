"""CLI command for sorting keys in a .env file."""
from __future__ import annotations
import click
from envoy.parser import parse_env_file, write_env_file, ParseError
from envoy.sorter import sort_env


@click.command("sort")
@click.argument("env_file", type=click.Path(exists=True))
@click.option(
    "--case-sensitive",
    is_flag=True,
    default=False,
    help="Sort with case sensitivity (uppercase before lowercase).",
)
@click.option(
    "--group",
    "groups",
    multiple=True,
    metavar="KEY",
    help="Keys to pin to the top (in order). Repeatable.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Print sorted output without writing to disk.",
)
def sort_cmd(
    env_file: str,
    case_sensitive: bool,
    groups: tuple,
    dry_run: bool,
) -> None:
    """Sort keys in ENV_FILE alphabetically."""
    try:
        env = parse_env_file(env_file)
    except ParseError as exc:
        raise click.ClickException(str(exc)) from exc

    group_list = [[k] for k in groups] if groups else None
    result = sort_env(env, groups=group_list, case_sensitive=case_sensitive)

    if not result.changed:
        click.echo("Keys are already in sorted order. Nothing to do.")
        return

    if dry_run:
        click.echo(f"# Sorted preview of {env_file}")
        for key, value in result.sorted_env.items():
            click.echo(f"{key}={value}")
        return

    write_env_file(env_file, result.sorted_env)
    click.echo(result.summary())
