"""CLI command: trace key provenance across multiple .env files."""
import click
from envoy.parser import parse_env_file
from envoy.tracer import trace_env


@click.command("trace")
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("--key", "-k", default=None, help="Show trace for a specific key only.")
@click.option("--show-overridden", is_flag=True, default=False, help="Also show shadowed entries.")
def trace_cmd(files, key, show_overridden):
    """Trace where each key originates across FILE(S) (later files override earlier)."""
    sources = {}
    for path in files:
        try:
            sources[path] = parse_env_file(path)
        except Exception as exc:
            raise click.ClickException(f"Failed to parse {path}: {exc}")

    result = trace_env(sources)

    if key:
        entries = [e for e in result.entries if e.key == key]
        if not entries:
            click.echo(f"Key '{key}' not found in any source.")
            raise SystemExit(1)
        for e in entries:
            status = f"(overridden by {e.overridden_by})" if e.overridden_by else "(active)"
            click.echo(f"  {e.source}: {e.key}={e.value}  {status}")
        return

    click.echo(f"Traced {len(result.env)} active keys across {len(result.sources)} files.")
    click.echo()

    active_entries = [e for e in result.entries if e.overridden_by is None]
    for e in sorted(active_entries, key=lambda x: x.key):
        click.echo(f"  {e.key}={e.value}  [{e.source}]")

    if show_overridden and result.overridden:
        click.echo()
        click.echo("Shadowed entries:")
        for e in result.overridden:
            click.echo(f"  {e.key}={e.value}  [{e.source}] -> overridden by {e.overridden_by}")
