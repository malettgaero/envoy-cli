"""CLI command: envoy pin-check – verify pinned key values against a .env file."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from envoy.parser import ParseError, parse_env_file
from envoy.pinner import pin_env


@click.command("pin-check")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "-p",
    "--pin",
    "pins",
    multiple=True,
    metavar="KEY=VALUE",
    required=True,
    help="Pin assertion in KEY=VALUE format. Repeatable.",
)
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Exit with code 1 on any violation (default: warn only).",
)
def pin_check_cmd(env_file: str, pins: tuple[str, ...], strict: bool) -> None:
    """Check that pinned KEY=VALUE pairs match exactly in ENV_FILE."""
    # Parse pin arguments
    pin_map: dict[str, str] = {}
    for raw in pins:
        if "=" not in raw:
            raise click.BadParameter(
                f"Pin {raw!r} must be in KEY=VALUE format.", param_hint="--pin"
            )
        key, _, value = raw.partition("=")
        pin_map[key.strip()] = value

    # Load env file
    try:
        env = parse_env_file(Path(env_file))
    except ParseError as exc:
        click.echo(f"Parse error: {exc}", err=True)
        sys.exit(2)

    result = pin_env(env, pin_map)

    if result.passed:
        click.echo(click.style(result.summary(), fg="green"))
    else:
        click.echo(click.style(result.summary(), fg="red"))
        for v in result.violations:
            click.echo(f"  {v}")
        if strict:
            sys.exit(1)
