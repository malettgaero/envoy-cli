import click
from envoy.parser import parse_env_file, ParseError
from envoy.stricter import strict_check


@click.command("strict")
@click.argument("env_file", type=click.Path(exists=True))
@click.option("--allow-lowercase", is_flag=True, default=False, help="Allow lowercase key names.")
@click.option("--allow-empty", is_flag=True, default=False, help="Allow empty values.")
@click.option("--max-length", type=int, default=None, help="Maximum allowed value length.")
@click.option("--forbid", multiple=True, help="Regex patterns forbidden in values.")
@click.option("--verbose", is_flag=True, default=False, help="Show per-key details.")
def strict_cmd(env_file, allow_lowercase, allow_empty, max_length, forbid, verbose):
    """Run strict validation checks on an .env file."""
    try:
        env = parse_env_file(env_file)
    except ParseError as e:
        raise click.ClickException(str(e))

    result = strict_check(
        env,
        require_uppercase=not allow_lowercase,
        disallow_empty=not allow_empty,
        max_value_length=max_length,
        forbidden_patterns=list(forbid),
    )

    if verbose:
        for key in sorted(env.keys()):
            key_violations = [v for v in result.violations if v.key == key]
            status = "FAIL" if key_violations else "OK"
            click.echo(f"  [{status}] {key}")
            for v in key_violations:
                click.echo(f"         -> {v.reason}")

    click.echo(result.summary())

    if not result.passed():
        if not verbose:
            for v in result.violations:
                click.echo(f"  {v}")
        raise SystemExit(1)
