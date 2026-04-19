"""CLI command for expiry checking of date-valued env keys."""
import click
from datetime import date
from envoy.parser import parse_env_file
from envoy.expirer import check_expiry


@click.command("expiry")
@click.argument("env_file", type=click.Path(exists=True))
@click.option("--key", "keys", multiple=True, help="Specific keys to check.")
@click.option("--warn-days", default=30, show_default=True, help="Days threshold for 'expiring soon' warning.")
@click.option("--strict", is_flag=True, help="Exit non-zero if any key is expired.")
def expiry_cmd(env_file: str, keys, warn_days: int, strict: bool) -> None:
    """Check date-valued keys for expiry or upcoming renewal."""
    env = parse_env_file(env_file)
    key_list = list(keys) if keys else None
    result = check_expiry(env, keys=key_list)

    if not result.entries and not result.skipped:
        click.echo("No date keys found.")
        return

    today = date.today()
    for entry in result.entries:
        if entry.expired:
            status = click.style("EXPIRED", fg="red")
        elif entry.days_remaining <= warn_days:
            status = click.style(f"EXPIRING IN {entry.days_remaining}d", fg="yellow")
        else:
            status = click.style("OK", fg="green")
        click.echo(f"  {entry.key:<30} {entry.value}  [{status}]")

    if result.skipped:
        for k in result.skipped:
            click.echo(click.style(f"  SKIP  {k} — not a recognised date", fg="yellow"))

    click.echo()
    click.echo(result.summary())

    if strict and not result.passed:
        raise SystemExit(1)
