"""CLI entry-point for envoy-cli."""

import sys
from pathlib import Path
from typing import List, Optional

import click

from envoy.diff import diff_envs
from envoy.merger import MergeError, Strategy, merge_envs
from envoy.parser import ParseError, parse_env_file, write_env_file
from envoy.validator import validate_env


@click.group()
def cli() -> None:
    """envoy-cli: manage and validate .env files."""


@cli.command("validate")
@click.argument("envfile", type=click.Path(exists=True))
@click.option("--allow-empty", is_flag=True, default=False, help="Allow empty values.")
def validate_cmd(envfile: str, allow_empty: bool) -> None:
    """Validate an .env file for common issues."""
    try:
        env = parse_env_file(Path(envfile))
    except ParseError as exc:
        click.echo(f"Parse error: {exc}", err=True)
        sys.exit(1)

    result = validate_env(env, allow_empty=allow_empty)
    click.echo(result.summary())
    if not result.is_valid:
        sys.exit(1)


@cli.command("diff")
@click.argument("base", type=click.Path(exists=True))
@click.argument("target", type=click.Path(exists=True))
@click.option("--mask-secrets", is_flag=True, default=False, help="Mask secret values.")
def diff_cmd(base: str, target: str, mask_secrets: bool) -> None:
    """Diff two .env files."""
    try:
        env_base = parse_env_file(Path(base))
        env_target = parse_env_file(Path(target))
    except ParseError as exc:
        click.echo(f"Parse error: {exc}", err=True)
        sys.exit(1)

    result = diff_envs(env_base, env_target, mask_secrets=mask_secrets)
    click.echo(result.summary())
    if result.has_changes:
        sys.exit(1)


@cli.command("list")
@click.argument("envfile", type=click.Path(exists=True))
@click.option("--keys-only", is_flag=True, default=False, help="Print only key names.")
def list_cmd(envfile: str, keys_only: bool) -> None:
    """List all keys (and optionally values) in an .env file."""
    try:
        env = parse_env_file(Path(envfile))
    except ParseError as exc:
        click.echo(f"Parse error: {exc}", err=True)
        sys.exit(1)

    for key, value in env.items():
        if keys_only:
            click.echo(key)
        else:
            click.echo(f"{key}={value}")


@cli.command("merge")
@click.argument("files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option("--output", "-o", type=click.Path(), default=None, help="Write merged output to file.")
@click.option(
    "--strategy",
    type=click.Choice([s.value for s in Strategy], case_sensitive=False),
    default=Strategy.LAST_WINS.value,
    show_default=True,
    help="Conflict resolution strategy.",
)
def merge_cmd(files: List[str], output: Optional[str], strategy: str) -> None:
    """Merge multiple .env files into one."""
    envs = []
    for filepath in files:
        try:
            env = parse_env_file(Path(filepath))
            envs.append((filepath, env))
        except ParseError as exc:
            click.echo(f"Parse error in {filepath}: {exc}", err=True)
            sys.exit(1)

    try:
        result = merge_envs(envs, strategy=Strategy(strategy))
    except MergeError as exc:
        click.echo(f"Merge error: {exc}", err=True)
        sys.exit(1)

    click.echo(result.summary())

    if output:
        write_env_file(Path(output), result.merged)
        click.echo(f"Written to {output}")
    else:
        for key, value in result.merged.items():
            click.echo(f"{key}={value}")

    if result.has_conflicts:
        sys.exit(2)
