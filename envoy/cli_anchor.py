"""CLI command: anchor — reorder .env keys with top/bottom anchors."""
import click
from envoy.parser import parse_env_file, write_env_file
from envoy.anchorer import anchor_env


@click.command("anchor")
@click.argument("env_file", type=click.Path(exists=True))
@click.option(
    "--top",
    "top_keys",
    multiple=True,
    metavar="KEY",
    help="Key(s) to anchor at the top (repeatable).",
)
@click.option(
    "--bottom",
    "bottom_keys",
    multiple=True,
    metavar="KEY",
    help="Key(s) to anchor at the bottom (repeatable).",
)
@click.option(
    "--group",
    "group_specs",
    multiple=True,
    metavar="NAME:KEY1,KEY2",
    help="Named group of keys, e.g. db:DB_HOST,DB_PORT (repeatable).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show reordering without writing the file.",
)
@click.option(
    "--quiet",
    is_flag=True,
    default=False,
    help="Suppress summary output.",
)
def anchor_cmd(env_file, top_keys, bottom_keys, group_specs, dry_run, quiet):
    """Reorder keys in ENV_FILE by anchoring specified keys to top or bottom."""
    env = parse_env_file(env_file)

    groups = {}
    for spec in group_specs:
        if ":" not in spec:
            raise click.BadParameter(f"Invalid group spec '{spec}', expected NAME:KEY1,KEY2")
        name, keys_str = spec.split(":", 1)
        groups[name.strip()] = [k.strip() for k in keys_str.split(",") if k.strip()]

    result = anchor_env(
        env,
        top_keys=list(top_keys),
        bottom_keys=list(bottom_keys),
        groups=groups,
    )

    if not quiet:
        click.echo(f"Anchor summary: {result.summary()}")
        if result.changed:
            click.echo("Order:")
            for key in result.order:
                pos = next(e.position for e in result.entries if e.key == key)
                tag = f"  [{pos}]" if pos != "free" else ""
                click.echo(f"  {key}{tag}")
        else:
            click.echo("No reordering needed.")

    if result.changed and not dry_run:
        write_env_file(env_file, result.env)
        if not quiet:
            click.echo(f"Written: {env_file}")
