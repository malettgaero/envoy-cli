"""CLI command: envoy score — display env quality score."""
from __future__ import annotations
import click
from envoy.parser import parse_env_file
from envoy.scorer import score_env


@click.command("score")
@click.argument("env_file", type=click.Path(exists=True))
@click.option("--no-penalise-empty", is_flag=True, default=False, help="Don't deduct for empty values.")
@click.option("--no-penalise-lowercase", is_flag=True, default=False, help="Don't deduct for lowercase keys.")
@click.option("--penalise-no-comment", is_flag=True, default=False, help="Deduct when key has no preceding comment.")
@click.option("--verbose", "-v", is_flag=True, default=False, help="Show per-key breakdown.")
def score_cmd(
    env_file: str,
    no_penalise_empty: bool,
    no_penalise_lowercase: bool,
    penalise_no_comment: bool,
    verbose: bool,
) -> None:
    """Score the quality of an .env file."""
    with open(env_file) as fh:
        raw_lines = fh.readlines()

    env = parse_env_file(env_file)
    result = score_env(
        env,
        lines=raw_lines if penalise_no_comment else None,
        penalise_empty=not no_penalise_empty,
        penalise_lowercase=not no_penalise_lowercase,
        penalise_no_comment=penalise_no_comment,
    )

    if verbose:
        for entry in result.entries:
            status = "OK" if not entry.deductions else ", ".join(entry.deductions)
            click.echo(f"  {entry.key:<30} {entry.points:>3}/10  [{status}]")
        click.echo()

    click.echo(result.summary())
    if result.grade in ("D", "F"):
        raise SystemExit(1)
