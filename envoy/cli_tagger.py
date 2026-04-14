"""CLI commands for tagging env keys."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

import click

from envoy.parser import parse_env_file
from envoy.tagger import tag_env


@click.group("tag")
def tag_cmd():
    """Tag env keys with labels for grouping and filtering."""


@tag_cmd.command("apply")
@click.argument("env_file", type=click.Path(exists=True))
@click.option(
    "--tag",
    "tags",
    multiple=True,
    metavar="KEY=LABEL",
    help="Assign a label to a key, e.g. DB_PASSWORD=secret. Repeatable.",
)
@click.option("--filter", "filter_tag", default=None, help="Show only keys with this tag.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def apply_cmd(env_file: str, tags: List[str], filter_tag: str | None, as_json: bool):
    """Apply tags to keys in ENV_FILE and display results."""
    env = parse_env_file(Path(env_file))

    tag_map: dict[str, list[str]] = {}
    for pair in tags:
        if "=" not in pair:
            raise click.BadParameter(f"Expected KEY=LABEL, got: {pair!r}")
        key, label = pair.split("=", 1)
        tag_map.setdefault(key.strip(), []).append(label.strip())

    result = tag_env(env, tag_map)

    entries = result.entries
    if filter_tag:
        entries = [e for e in entries if filter_tag in e.tags]

    if as_json:
        click.echo(json.dumps([e.to_dict() for e in entries], indent=2))
        return

    if not entries:
        click.echo("No matching keys.")
        return

    for entry in entries:
        tag_str = ", ".join(sorted(entry.tags)) if entry.tags else "(none)"
        click.echo(f"  {entry.key:<30} [{tag_str}]")

    click.echo()
    click.echo(result.summary())
