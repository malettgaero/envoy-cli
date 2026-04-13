"""CLI commands for template rendering of .env files."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from envoy.parser import ParseError, parse_env_file, write_env_file
from envoy.templater import TemplateError, render_env


@click.command("template")
@click.argument("template_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("context_file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--output", "-o",
    type=click.Path(dir_okay=False),
    default=None,
    help="Write rendered output to FILE instead of stdout.",
)
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Exit with error if any placeholder cannot be resolved.",
)
def template_cmd(
    template_file: str,
    context_file: str,
    output: str | None,
    strict: bool,
) -> None:
    """Render TEMPLATE_FILE using values from CONTEXT_FILE.

    Placeholders use ``{{ KEY }}`` syntax.  CONTEXT_FILE is a plain .env file
    whose keys supply the substitution values.
    """
    try:
        tmpl = parse_env_file(Path(template_file))
        ctx = parse_env_file(Path(context_file))
    except ParseError as exc:
        click.echo(f"Parse error: {exc}", err=True)
        sys.exit(1)

    try:
        result = render_env(tmpl, ctx, strict=strict)
    except TemplateError as exc:
        click.echo(f"Template error: {exc}", err=True)
        sys.exit(1)

    if result.resolved:
        click.echo(
            f"Resolved {len(result.resolved)} placeholder(s): "
            + ", ".join(result.resolved),
            err=True,
        )
    if result.unresolved:
        click.echo(
            f"Warning: {len(result.unresolved)} placeholder(s) unresolved: "
            + ", ".join(result.unresolved),
            err=True,
        )

    if output:
        write_env_file(Path(output), result.rendered)
        click.echo(f"Rendered env written to {output}", err=True)
    else:
        for key, value in result.rendered.items():
            click.echo(f"{key}={value}")
