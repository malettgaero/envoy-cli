"""CLI entry-point for envoy-cli using Click."""

import sys
from pathlib import Path

import click

from envoy.parser import parse_env_file, ParseError, write_env_file
from envoy.diff import diff_envs


@click.group()
@click.version_option("0.1.0", prog_name="envoy")
def cli() -> None:
    """envoy — manage and validate .env files across environments."""


@cli.command("validate")
@click.argument("env_file", default=".env", metavar="FILE")
def validate_cmd(env_file: str) -> None:
    """Validate syntax of a .env FILE (default: .env)."""
    try:
        data = parse_env_file(env_file)
        click.secho(
            f"✔  {env_file} is valid ({len(data)} keys)", fg="green"
        )
    except FileNotFoundError as exc:
        click.secho(str(exc), fg="red", err=True)
        sys.exit(1)
    except ParseError as exc:
        click.secho(str(exc), fg="red", err=True)
        sys.exit(1)


@cli.command("diff")
@click.argument("base_file", metavar="BASE")
@click.argument("target_file", metavar="TARGET")
@click.option(
    "--no-mask",
    is_flag=True,
    default=False,
    help="Show secret values in plain text (use with caution).",
)
def diff_cmd(base_file: str, target_file: str, no_mask: bool) -> None:
    """Diff two .env files: BASE vs TARGET."""
    try:
        base = parse_env_file(base_file)
        target = parse_env_file(target_file)
    except (FileNotFoundError, ParseError) as exc:
        click.secho(str(exc), fg="red", err=True)
        sys.exit(1)

    result = diff_envs(base, target, mask_secrets=not no_mask)

    click.echo(f"Comparing {base_file} → {target_file}")
    click.echo(result.summary())

    if result.has_changes:
        sys.exit(1)  # non-zero exit so CI pipelines can detect drift


@cli.command("list")
@click.argument("env_file", default=".env", metavar="FILE")
@click.option("--mask", is_flag=True, default=False, help="Mask secret values.")
def list_cmd(env_file: str, mask: bool) -> None:
    """List all key-value pairs in a .env FILE."""
    try:
        data = parse_env_file(env_file)
    except (FileNotFoundError, ParseError) as exc:
        click.secho(str(exc), fg="red", err=True)
        sys.exit(1)

    for key, value in data.items():
        display = f"{key}={'*' * len(value)}" if mask else f"{key}={value}"
        click.echo(display)


if __name__ == "__main__":
    cli()
