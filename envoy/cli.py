"""CLI entry-point for envoy-cli."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from envoy.parser import parse_env_file, ParseError
from envoy.diff import diff_envs
from envoy.validator import validate_env


@click.group()
def cli() -> None:
    """envoy — manage and validate .env files."""


@cli.command("validate")
@click.argument("env_file", type=click.Path(exists=True))
@click.option(
    "--template", "-t",
    type=click.Path(exists=True),
    default=None,
    help="Template file (e.g. .env.example) to check required keys against.",
)
@click.option(
    "--allow-empty", is_flag=True, default=False,
    help="Do not flag keys with empty values.",
)
@click.option(
    "--strict", is_flag=True, default=False,
    help="Flag keys not present in the template as extra.",
)
def validate_cmd(
    env_file: str,
    template: str | None,
    allow_empty: bool,
    strict: bool,
) -> None:
    """Validate ENV_FILE for correctness."""
    try:
        env = parse_env_file(Path(env_file))
        tmpl = parse_env_file(Path(template)) if template else None
    except ParseError as exc:
        click.echo(f"Parse error: {exc}", err=True)
        sys.exit(1)

    result = validate_env(env, template=tmpl, allow_empty=allow_empty, strict=strict)
    click.echo(result.summary())
    sys.exit(0 if result.is_valid else 1)


@cli.command("diff")
@click.argument("base_file", type=click.Path(exists=True))
@click.argument("compare_file", type=click.Path(exists=True))
@click.option("--mask-secrets", is_flag=True, default=True, help="Mask secret values.")
def diff_cmd(base_file: str, compare_file: str, mask_secrets: bool) -> None:
    """Show diff between BASE_FILE and COMPARE_FILE."""
    try:
        base = parse_env_file(Path(base_file))
        compare = parse_env_file(Path(compare_file))
    except ParseError as exc:
        click.echo(f"Parse error: {exc}", err=True)
        sys.exit(1)

    result = diff_envs(base, compare, mask_secrets=mask_secrets)
    click.echo(result.summary())
    sys.exit(0 if not result.has_changes else 1)


@cli.command("list")
@click.argument("env_file", type=click.Path(exists=True))
@click.option("--mask-secrets", is_flag=True, default=False)
def list_cmd(env_file: str, mask_secrets: bool) -> None:
    """List all key-value pairs in ENV_FILE."""
    try:
        env = parse_env_file(Path(env_file))
    except ParseError as exc:
        click.echo(f"Parse error: {exc}", err=True)
        sys.exit(1)

    for key, value in sorted(env.items()):
        display = "****" if mask_secrets else value
        click.echo(f"{key}={display}")


if __name__ == "__main__":
    cli()
