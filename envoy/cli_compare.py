"""CLI command: compare multiple .env files side-by-side."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List

import click

from envoy.comparator import compare_envs
from envoy.parser import parse_env_file, ParseError


@click.command("compare")
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option(
    "--mask", is_flag=True, default=False, help="Mask all values with *** in output."
)
@click.option(
    "--only-issues",
    is_flag=True,
    default=False,
    help="Show only inconsistent or missing keys.",
)
def compare_cmd(files: List[str], mask: bool, only_issues: bool) -> None:
    """Compare N .env FILES side-by-side and highlight differences."""
    if len(files) < 2:
        click.echo("Error: at least two files are required for comparison.", err=True)
        sys.exit(1)

    envs = {}
    for path_str in files:
        path = Path(path_str)
        try:
            envs[path.name] = parse_env_file(path)
        except ParseError as exc:
            click.echo(f"Parse error in {path}: {exc}", err=True)
            sys.exit(1)

    result = compare_envs(envs, mask_secrets=mask)

    click.echo(result.summary())
    click.echo()

    entries = result.inconsistent_entries if only_issues else result.entries
    if not entries:
        click.echo("All keys are consistent across environments.")
        return

    # Column widths
    key_width = max(len(e.key) for e in entries)
    col_width = max(20, *(len(n) for n in result.env_names))

    header = f"{'KEY':<{key_width}}  " + "  ".join(
        f"{n:<{col_width}}" for n in result.env_names
    )
    click.echo(header)
    click.echo("-" * len(header))

    for entry in entries:
        row_vals = []
        for name in result.env_names:
            val = entry.values.get(name)
            cell = "<missing>" if val is None else val
            row_vals.append(f"{cell:<{col_width}}")
        flag = "" if entry.is_consistent else "  *"
        click.echo(f"{entry.key:<{key_width}}  {'  '.join(row_vals)}{flag}")
