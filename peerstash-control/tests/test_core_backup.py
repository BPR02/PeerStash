import pytest
from pytest_mock import MockType

from peerstash.core.backup import (
    get_snapshots,
    mount_task,
    prune_repo,
    remove_schedule,
    restore_snapshot,
    run_backup,
    schedule_backup,
    unmount_task,
)


def test_schedule_backup_valid_new_task(mock_db, mock_daemon_and_locks):
    task_name = schedule_backup(
        paths=["/var/www/html"], peer="node1", name="web_backup"
    )
    assert task_name == "web_backup"
    assert mock_db["tasks"]["web_backup"].hostname == "peerstash-node1"


def test_schedule_backup_invalid_cron(mock_db, mock_daemon_and_locks):
    with pytest.raises(ValueError, match="invalid"):
        schedule_backup(
            paths=["/var/www/html"], peer="node1", schedule="invalid_cron_string"
        )


def test_run_backup_dry_run(
    mock_db, mock_daemon_and_locks, mock_restic, mock_subprocess
):
    schedule_backup(paths=["/test"], peer="node1", name="test_bkp")
    res = run_backup("test_bkp", dry_run=True, offset=0)

    assert res is not None
    assert res["data_added"] == 1048576


def test_run_backup_init_storage_full(
    mock_db, mock_daemon_and_locks, mock_restic, mock_subprocess, monkeypatch
):
    schedule_backup(paths=["/test"], peer="node1", name="test_bkp")

    # Trigger the full disk sftp mock output via environment variable
    monkeypatch.setenv("MOCK_DISK_FULL", "1")

    with pytest.raises(
        RuntimeError, match="Not enough storage to create initial backup"
    ):
        run_backup("test_bkp", offset=0)

    assert mock_db["tasks"]["test_bkp"].status == "idle"
    assert mock_db["tasks"]["test_bkp"].last_exit_code == 2


def test_run_backup_success(
    mock_db, mock_daemon_and_locks, mock_restic, mock_subprocess
):
    schedule_backup(paths=["/test"], peer="node1", name="test_bkp")
    mock_db["tasks"]["test_bkp"].status = "idle"

    res = run_backup("test_bkp", offset=0)

    assert res is not None
    assert res["snapshot_id"] == "snap123"


def test_prune_repo_success(
    mock_db, mock_daemon_and_locks, mock_restic, mock_subprocess
):
    schedule_backup(paths=["/test"], peer="node1", name="test_bkp")
    mock_db["tasks"]["test_bkp"].status = "idle"

    try:
        prune_repo("test_bkp", offset=0, repack=True)
    except Exception as e:
        pytest.fail(f"prune_repo failed unexpectedly: {e}")


def test_remove_schedule_existing(mock_db, mock_daemon_and_locks, mock_subprocess):
    schedule_backup(paths=["/test"], peer="node1", name="test_bkp")
    remove_schedule("test_bkp")
    assert "test_bkp" not in mock_db["tasks"]


def test_restore_snapshot_failure(
    mock_db, mock_daemon_and_locks, mock_restic, mock_subprocess, monkeypatch
):
    schedule_backup(paths=["/test"], peer="node1", name="test_bkp")
    mock_db["tasks"]["test_bkp"].status = "idle"

    # Trigger the restic restore failure mock via environment variable
    monkeypatch.setenv("MOCK_RESTORE_FAIL", "1")

    with pytest.raises(Exception, match="Failed to restore snapshot"):
        restore_snapshot("test_bkp", snapshot="latest")


# --- Schedule Edge Cases ---
def test_schedule_backup_invalid_paths(mock_db, mock_daemon_and_locks):
    # Escaping the root backup target fails
    with pytest.raises(ValueError, match="invalid path"):
        schedule_backup(paths=["../../sys/class"], peer="node1")


def test_schedule_backup_invalid_retention(mock_db, mock_daemon_and_locks):
    with pytest.raises(ValueError, match="Retention 'invalid' invalid"):
        schedule_backup(paths=["/test"], peer="node1", retention="invalid")


def test_schedule_backup_update_existing(mock_db, mock_daemon_and_locks):
    schedule_backup(paths=["/test"], peer="node1", name="test_bkp")
    # Schedule again with a new retention policy
    schedule_backup(paths=["/test"], peer="node1", name="test_bkp", retention="1y")
    assert mock_db["tasks"]["test_bkp"].retention == "1y"


# --- Run Backup Failure Modes ---
def test_run_backup_restic_failure(
    mock_db, mock_daemon_and_locks, mock_restic, mock_subprocess
):
    # restic_mock.py is programmed to fail if '/forbidden_path' is included
    schedule_backup(paths=["/forbidden_path"], peer="node1", name="fail_bkp")
    mock_db["tasks"]["fail_bkp"].status = "idle"

    with pytest.raises(RuntimeError, match="Backup failed!"):
        run_backup("fail_bkp", offset=0)
    assert mock_db["tasks"]["fail_bkp"].last_exit_code == 3


def test_run_backup_corrupted_repo(
    mock_db, mock_daemon_and_locks, mock_restic, mock_subprocess, monkeypatch
):
    schedule_backup(paths=["/test"], peer="node1", name="corrupt_bkp")
    mock_db["tasks"]["corrupt_bkp"].status = "idle"

    # restic_mock.py is programmed to fail check if 'corrupted' is in the repo path/env
    monkeypatch.setenv("RESTIC_REPOSITORY", "corrupted")

    with pytest.raises(RuntimeError, match="Repository.*is corrupted"):
        run_backup("corrupt_bkp", offset=0)
    assert mock_db["tasks"]["corrupt_bkp"].last_exit_code == 4


# --- Prune Edge Cases ---
def test_prune_repo_new_task(mock_db, mock_daemon_and_locks):
    schedule_backup(paths=["/test"], peer="node1", name="test_bkp")
    # Task status is 'new' by default
    with pytest.raises(RuntimeError, match="has not been backed up yet"):
        prune_repo("test_bkp")


# --- Snapshots, Mount, Unmount ---
def test_get_snapshots_success(mock_db, mock_restic):
    schedule_backup(paths=["/test"], peer="node1", name="test_bkp")
    snaps = get_snapshots("test_bkp")
    assert len(snaps) > 0
    assert snaps[0]["id"] == "snap123"


def test_mount_and_unmount_task(mock_db, mock_subprocess, mock_popen: MockType):
    schedule_backup(paths=["/test"], peer="node1", name="test_bkp")

    mount_task("test_bkp")

    # Assert directly on the injected mock object, keeping type checkers happy
    mock_popen.assert_called_once()

    # Test unmount (handled naturally by our subprocess_router returning a 0 exit code)
    try:
        unmount_task("test_bkp")
    except Exception as e:
        pytest.fail(f"unmount_task failed: {e}")
