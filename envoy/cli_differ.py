"""CLI command for line-level .env file diffing."""
import click
from envoy.differ import diff_lines

_COLORS = {
    "insert": "green",
    "delete": "red",
    "equal": None,
}

_PREFIXES = {
    "insert": "+ ",
    "delete": "- ",
    "equal": "  ",
}


@click.command("linediff")
@click.argument("file_a", type=click.Path(exists=True))
@click.argument("file_b", type=click.Path(exists=True))
@click.option("--no-color", is_flag=True, default=False, help="Disable colored output.")
@click.option("--only-changes", is_flag=True, default=False, help="Show only changed lines.")
def linediff_cmd(file_a: str, file_b: str, no_color: bool, only_changes: bool) -> None:
    """Show a line-level diff between FILE_A and FILE_B."""
    with open(file_a) as f:
        text_a = f.read()
    with open(file_b) as f:
        text_b = f.read()

    report = diff_lines(text_a, text_b)

    if not report.has_changes:
        click.echo("No differences found.")
        return

    for line in report.lines:
        if only_changes and line.tag == "equal":
            continue
        prefix = _PREFIXES.get(line.tag, "  ")
        text = prefix + line.content
        color = None if no_color else _COLORS.get(line.tag)
        if color:
            click.echo(click.style(text, fg=color))
        else:
            click.echo(text)

    click.echo()
    click.echo(report.summary())
