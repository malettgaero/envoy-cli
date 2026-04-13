"""Tests for envoy.snapshot."""
import json
from pathlib import Path

import pytest

from envoy.snapshot import Snapshot, SnapshotStore


@pytest.fixture
def env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("APP=prod\nDEBUG=false\nSECRET=abc123\n")
    return str(f)


@pytest.fixture
def store(tmp_path):
    return SnapshotStore(path=tmp_path / "snapshots.json")


def test_take_creates_snapshot(store, env_file):
    snap = store.take(env_file, label="v1")
    assert snap.label == "v1"
    assert snap.env["APP"] == "prod"
    assert snap.env["DEBUG"] == "false"


def test_take_persists_to_disk(store, env_file, tmp_path):
    store.take(env_file, label="v1")
    raw = json.loads((tmp_path / "snapshots.json").read_text())
    assert len(raw) == 1
    assert raw[0]["label"] == "v1"


def test_list_returns_all_snapshots(store, env_file):
    store.take(env_file, label="v1")
    store.take(env_file, label="v2")
    snaps = store.list_snapshots()
    assert len(snaps) == 2
    assert [s.label for s in snaps] == ["v1", "v2"]


def test_get_returns_correct_snapshot(store, env_file):
    store.take(env_file, label="alpha")
    store.take(env_file, label="beta")
    snap = store.get("alpha")
    assert snap is not None
    assert snap.label == "alpha"


def test_get_returns_none_for_missing_label(store, env_file):
    store.take(env_file, label="v1")
    assert store.get("nonexistent") is None


def test_restore_writes_env_file(store, env_file, tmp_path):
    store.take(env_file, label="snap1")
    out = str(tmp_path / "restored.env")
    store.restore("snap1", out)
    content = Path(out).read_text()
    assert "APP=prod" in content
    assert "DEBUG=false" in content


def test_restore_raises_for_unknown_label(store, env_file, tmp_path):
    store.take(env_file, label="v1")
    with pytest.raises(KeyError, match="missing"):
        store.restore("missing", str(tmp_path / "out.env"))


def test_delete_removes_snapshot(store, env_file):
    store.take(env_file, label="v1")
    store.take(env_file, label="v2")
    result = store.delete("v1")
    assert result is True
    assert store.get("v1") is None
    assert store.get("v2") is not None


def test_delete_returns_false_for_missing(store, env_file):
    store.take(env_file, label="v1")
    assert store.delete("ghost") is False


def test_store_loads_existing_file(env_file, tmp_path):
    store1 = SnapshotStore(path=tmp_path / "snaps.json")
    store1.take(env_file, label="persisted")
    store2 = SnapshotStore(path=tmp_path / "snaps.json")
    assert len(store2.list_snapshots()) == 1
    assert store2.get("persisted") is not None
