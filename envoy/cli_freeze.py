"""CLI commands for freeze / verify."""
import click
from pathlib import Path

from envoy.parser import parse_env_file
from envoy.freezer import freeze_env, verify_env, save_freeze, load_checksum


@click.group("freeze")
def freeze_cmd():
    """Freeze and verify .env file integrity."""


@freeze_cmd.command("lock")
@click.argument("env_file", type=click.Path(exists=True))
@click.option("--lock-file", default=None, help="Path to write the lock file (default: <env_file>.lock)")
def lock_cmd(env_file: str, lock_file: str | None):
    """Freeze ENV_FILE and write a checksum lock file."""
    src = Path(env_file)
    lock = Path(lock_file) if lock_file else src.with_suffix(src.suffix + ".lock")
    env = parse_env_file(src)
    result = freeze_env(env)
    save_freeze(result, lock)
    click.echo(f"Frozen: {src}")
    click.echo(f"Checksum: {result.checksum}")
    click.echo(f"Lock file: {lock}")


@freeze_cmd.command("verify")
@click.argument("env_file", type=click.Path(exists=True))
@click.option("--lock-file", default=None, help="Path to the lock file (default: <env_file>.lock)")
@click.option("--strict", is_flag=True, help="Exit with non-zero code if tampered.")
def verify_cmd(env_file: str, lock_file: str | None, strict: bool):
    """Verify ENV_FILE against its checksum lock."""
    src = Path(env_file)
    lock = Path(lock_file) if lock_file else src.with_suffix(src.suffix + ".lock")
    checksum = load_checksum(lock)
    if checksum is None:
        click.echo(f"No lock file found at {lock}", err=True)
        raise SystemExit(1)
    env = parse_env_file(src)
    result = verify_env(env, checksum)
    click.echo(result.summary())
    if strict and not result.passed:
        raise SystemExit(1)
