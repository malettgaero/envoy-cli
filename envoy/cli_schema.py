"""CLI sub-command: schema-validate — check a .env file against a JSON schema spec."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from envoy.parser import parse_env_file, ParseError
from envoy.schema import load_schema_from_dict, validate_schema


@click.command("schema-validate")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("schema_file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Exit with non-zero status on any violation.",
)
def schema_validate_cmd(env_file: str, schema_file: str, strict: bool) -> None:
    """Validate ENV_FILE against the JSON schema defined in SCHEMA_FILE.

    SCHEMA_FILE must be a JSON file mapping key names to field specs::

        {
          "APP_ENV": {"required": true, "allowed_values": ["dev", "prod"]},
          "PORT":    {"required": false, "pattern": "\\\\d{4,5}"}
        }
    """
    # --- parse .env ---
    try:
        env = parse_env_file(Path(env_file))
    except ParseError as exc:
        click.echo(f"Parse error: {exc}", err=True)
        sys.exit(1)

    # --- load schema ---
    try:
        raw_schema = json.loads(Path(schema_file).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        click.echo(f"Schema load error: {exc}", err=True)
        sys.exit(1)

    if not isinstance(raw_schema, dict):
        click.echo("Schema file must contain a JSON object at the top level.", err=True)
        sys.exit(1)

    schema = load_schema_from_dict(raw_schema)
    result = validate_schema(env, schema)

    click.echo(result.summary())

    if strict and not result.is_valid:
        sys.exit(1)
