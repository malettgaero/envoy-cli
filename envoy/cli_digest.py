"""CLI command: digest — show per-key hashes for a .env file."""
import click
from envoy.parser import parse_env_file
from envoy.digester import digest_env, DigestError


@click.command("digest")
@click.argument("env_file", type=click.Path(exists=True))
@click.option(
    "--algo",
    default="sha256",
    show_default=True,
    help="Hash algorithm: md5, sha1, sha256, sha512",
)
@click.option(
    "--key",
    "keys",
    multiple=True,
    help="Limit to specific key(s). Repeatable.",
)
@click.option("--short", is_flag=True, help="Show only first 12 chars of digest.")
def digest_cmd(env_file: str, algo: str, keys: tuple, short: bool) -> None:
    """Print a hash digest for each value in ENV_FILE."""
    env = parse_env_file(env_file)
    selected = list(keys) if keys else None

    try:
        result = digest_env(env, algorithm=algo, keys=selected)
    except DigestError as exc:
        raise click.ClickException(str(exc))

    if not result.entries:
        click.echo("No keys to digest.")
        return

    for entry in result.entries:
        digest = entry.digest[:12] if short else entry.digest
        click.echo(f"{entry.key}  [{entry.algorithm}]  {digest}")

    click.echo(f"\n{result.summary()}")
