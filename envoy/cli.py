"""Entry-point for the envoy CLI."""
import click

from envoy.cli_schema import schema_validate_cmd
from envoy.cli_template import template_cmd
from envoy.parser import ParseError, parse_env_file
from envoy.diff import diff_envs
from envoy.validator import validate_env
from envoy.merger import Strategy, merge_envs
from envoy.history import show_history


@click.group()
def cli() -> None:  # noqa: D401
    """envoy — manage and validate .env files."""


@cli.command("validate")
@click.argument("env_file", type=click.Path(exists=True))
@click.option("--allow-empty", is_flag=True, default=False)
def validate_cmd(env_file: str, allow_empty: bool) -> None:
    """Validate an .env file."""
    import sys
    from pathlib import Path

    try:
        env = parse_env_file(Path(env_file))
    except ParseError as exc:
        click.echo(f"Parse error: {exc}", err=True)
        sys.exit(1)

    result = validate_env(env, allow_empty=allow_empty)
    click.echo(result.summary())
    if not result.is_valid:
        sys.exit(1)


@cli.command("diff")
@click.argument("base_file", type=click.Path(exists=True))
@click.argument("head_file", type=click.Path(exists=True))
@click.option("--mask-secrets", is_flag=True, default=False)
def diff_cmd(base_file: str, head_file: str, mask_secrets: bool) -> None:
    """Diff two .env files."""
    from pathlib import Path

    base = parse_env_file(Path(base_file))
    head = parse_env_file(Path(head_file))
    result = diff_envs(base, head, mask_secrets=mask_secrets)
    click.echo(result.summary())


@cli.command("list")
@click.argument("env_file", type=click.Path(exists=True))
@click.option("--mask", is_flag=True, default=False)
def list_cmd(env_file: str, mask: bool) -> None:
    """List keys (and optionally masked values) in an .env file."""
    from pathlib import Path

    env = parse_env_file(Path(env_file))
    for key, value in env.items():
        display = "***" if mask else value
        click.echo(f"{key}={display}")


@cli.command("merge")
@click.argument("env_files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option("--strategy", type=click.Choice(["last", "first", "error"]), default="error")
@click.option("--output", "-o", type=click.Path(), default=None)
def merge_cmd(env_files: tuple, strategy: str, output: str | None) -> None:
    """Merge multiple .env files."""
    import sys
    from pathlib import Path
    from envoy.parser import write_env_file

    strat = Strategy(strategy)
    envs = [parse_env_file(Path(f)) for f in env_files]
    result = merge_envs(envs, strategy=strat)
    if result.has_conflicts:
        for c in result.conflicts:
            click.echo(f"Conflict: {c}", err=True)
        if strat == Strategy.ERROR:
            sys.exit(1)
    if output:
        write_env_file(Path(output), result.merged)
    else:
        for key, value in result.merged.items():
            click.echo(f"{key}={value}")


@cli.command("history")
@click.option("--audit-file", default=".envoy_audit.json")
@click.option("--key", default=None)
@click.option("--action", default=None)
def history_cmd(audit_file: str, key: str | None, action: str | None) -> None:
    """Show audit history."""
    from pathlib import Path

    show_history(Path(audit_file), key_filter=key, action_filter=action)


cli.add_command(schema_validate_cmd, name="schema-validate")
cli.add_command(template_cmd, name="template")
