"""CLI commands for snapshot management."""
from pathlib import Path

import click

from envoy.snapshot import SnapshotStore

DEFAULT_STORE = ".envoy_snapshots.json"


def _get_store(store_path: str) -> SnapshotStore:
    return SnapshotStore(path=Path(store_path))


@click.group("snapshot")
@click.option("--store", default=DEFAULT_STORE, show_default=True, help="Snapshot store file.")
@click.pass_context
def snapshot_cmd(ctx: click.Context, store: str) -> None:
    """Manage .env file snapshots."""
    ctx.ensure_object(dict)
    ctx.obj["store"] = store


@snapshot_cmd.command("take")
@click.argument("env_file")
@click.option("--label", default=None, help="Human-readable label for the snapshot.")
@click.pass_context
def take_cmd(ctx: click.Context, env_file: str, label: str) -> None:
    """Capture a snapshot of ENV_FILE."""
    store = _get_store(ctx.obj["store"])
    snap = store.take(env_file, label=label)
    click.echo(f"Snapshot '{snap.label}' saved from {env_file} ({len(snap.env)} keys).")


@snapshot_cmd.command("list")
@click.pass_context
def list_cmd(ctx: click.Context) -> None:
    """List all stored snapshots."""
    store = _get_store(ctx.obj["store"])
    snaps = store.list_snapshots()
    if not snaps:
        click.echo("No snapshots found.")
        return
    for snap in snaps:
        click.echo(f"  [{snap.timestamp}]  {snap.label!r}  ({snap.source})  {len(snap.env)} keys")


@snapshot_cmd.command("restore")
@click.argument("label")
@click.argument("output_file")
@click.pass_context
def restore_cmd(ctx: click.Context, label: str, output_file: str) -> None:
    """Restore snapshot LABEL to OUTPUT_FILE."""
    store = _get_store(ctx.obj["store"])
    try:
        snap = store.restore(label, output_file)
        click.echo(f"Restored '{snap.label}' -> {output_file} ({len(snap.env)} keys).")
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc


@snapshot_cmd.command("delete")
@click.argument("label")
@click.pass_context
def delete_cmd(ctx: click.Context, label: str) -> None:
    """Delete a snapshot by LABEL."""
    store = _get_store(ctx.obj["store"])
    removed = store.delete(label)
    if removed:
        click.echo(f"Snapshot '{label}' deleted.")
    else:
        raise click.ClickException(f"Snapshot '{label}' not found.")
