import subprocess
from datetime import datetime

import pytest
from pytest import MonkeyPatch
from pytest_mock import MockerFixture, MockType

from peerstash.core.backup import (_init_repo, _sftp_recursive_remove,
                                   _verify_backup_size, get_snapshots,
                                   mount_task, prune_repo, remove_schedule,
                                   restore_snapshot, run_backup,
                                   schedule_backup, unmount_task)


def test_schedule_backup_valid_new_task(mock_db, mock_daemon_and_locks):
    task_name = schedule_backup(
        paths=["/var/www/html"], peer="node1", name="web_backup"
    )
    assert task_name == "web_backup"
    assert mock_db["tasks"]["web_backup"].hostname == "peerstash-node1"


def test_schedule_backup_invalid_cron(mock_db, mock_daemon_and_locks):
    with pytest.raises(ValueError, match="(?i)invalid"):
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
    mock_db,
    mock_daemon_and_locks,
    mock_restic,
    mock_subprocess,
    monkeypatch: MonkeyPatch,
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


def test_remove_schedule_existing_new(mock_db, mock_daemon_and_locks, mock_subprocess):
    schedule_backup(paths=["/test"], peer="node1", name="test_bkp")
    remove_schedule("test_bkp")
    assert "test_bkp" not in mock_db["tasks"]


def test_remove_schedule_existing_not_new(
    mock_db, mock_daemon_and_locks, mock_subprocess, mocker: MockerFixture
):
    mock_sftp_remove = mocker.patch("peerstash.core.backup._sftp_recursive_remove")

    schedule_backup(paths=["/test"], peer="node1", name="test_bkp")
    mock_db["tasks"]["test_bkp"].status = "idle"
    remove_schedule("test_bkp")
    assert "test_bkp" not in mock_db["tasks"]

    assert "test_bkp" not in mock_db["tasks"]
    mock_sftp_remove.assert_called_once_with("peerstash-node1", "test_bkp")


def test_restore_snapshot_failure(
    mock_db,
    mock_daemon_and_locks,
    mock_restic,
    mock_subprocess,
    monkeypatch: MonkeyPatch,
):
    schedule_backup(paths=["/test"], peer="node1", name="test_bkp")
    mock_db["tasks"]["test_bkp"].status = "idle"

    # Trigger the restic restore failure mock via environment variable
    monkeypatch.setenv("MOCK_RESTORE_FAIL", "1")

    with pytest.raises(Exception, match="Failed to restore snapshot"):
        restore_snapshot("test_bkp", snapshot="latest")


# --- Schedule Edge Cases ---
def test_schedule_backup_unknown_peer(mock_db, mock_daemon_and_locks):
    # Escaping the root backup target fails
    with pytest.raises(ValueError, match="Peer .* does not exist"):
        schedule_backup(paths=["."], peer="no_peer")


def test_schedule_backup_invalid_paths(mock_db, mock_daemon_and_locks):
    # Escaping the root backup target fails
    with pytest.raises(ValueError, match="invalid path"):
        schedule_backup(paths=["../../sys/class"], peer="node1")


def test_schedule_backup_invalid_schedule(mock_db, mock_daemon_and_locks):
    # Escaping the root backup target fails
    with pytest.raises(ValueError, match="cron schedule .* is invalid"):
        schedule_backup(paths=["."], peer="node1", schedule="0")


def test_schedule_backup_invalid_prune_schedule(mock_db, mock_daemon_and_locks):
    # Escaping the root backup target fails
    with pytest.raises(ValueError, match="cron prune schedule .* is invalid"):
        schedule_backup(paths=["."], peer="node1", prune_schedule="0")


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
    mock_db,
    mock_daemon_and_locks,
    mock_restic,
    mock_subprocess,
    monkeypatch: MonkeyPatch,
):
    # restic_mock.py is programmed to fail if '/forbidden_path' is included
    schedule_backup(paths=["/forbidden_path"], peer="node1", name="fail_bkp")
    mock_db["tasks"]["fail_bkp"].status = "idle"
    monkeypatch.setenv("MOCK_BACKUP_FAIL", "1")

    with pytest.raises(RuntimeError, match="Backup failed!"):
        run_backup("fail_bkp", offset=0)
    assert mock_db["tasks"]["fail_bkp"].last_exit_code == 3


def test_run_backup_corrupted_repo(
    mock_db,
    mock_daemon_and_locks,
    mock_restic,
    mock_subprocess,
    monkeypatch: MonkeyPatch,
):
    schedule_backup(paths=["/test"], peer="node1", name="corrupt_bkp")
    mock_db["tasks"]["corrupt_bkp"].status = "idle"

    # restic_mock.py is programmed to fail check if 'corrupted' is in the repo path/env
    monkeypatch.setenv("RESTIC_REPOSITORY", "corrupted")

    with pytest.raises(RuntimeError, match="(?i)Repository.*is corrupted"):
        run_backup("corrupt_bkp", offset=0)
    assert mock_db["tasks"]["corrupt_bkp"].last_exit_code == 4


# --- Prune Edge Cases ---
def test_prune_repo_new_task(mock_db, mock_daemon_and_locks):
    schedule_backup(paths=["/test"], peer="node1", name="test_bkp")
    # Task status is 'new' by default
    with pytest.raises(RuntimeError, match="has not been backed up yet"):
        prune_repo("test_bkp")


# --- Snapshots, Mount, Unmount ---
def test_get_snapshots_success(mock_db, mock_daemon_and_locks, mock_restic):
    schedule_backup(paths=["/test"], peer="node1", name="test_bkp")
    snaps = get_snapshots("test_bkp")
    assert len(snaps) > 0
    assert snaps[0]["id"] == "snap123"


def test_mount_and_unmount_task(
    mock_db, mock_daemon_and_locks, mock_subprocess, mock_popen: MockType
):
    schedule_backup(paths=["/test"], peer="node1", name="test_bkp")

    mount_task("test_bkp")

    # Assert directly on the injected mock object, keeping type checkers happy
    mock_popen.assert_called_once()

    # Test unmount (handled naturally by our subprocess_router returning a 0 exit code)
    try:
        unmount_task("test_bkp")
    except Exception as e:
        pytest.fail(f"unmount_task failed: {e}")


import subprocess
from datetime import datetime

import pytest

# Import the module itself so we can access the patched DB functions
import peerstash.core.backup as backup_mod
from peerstash.core.backup import (_init_repo, _sftp_recursive_remove,
                                   _verify_backup_size, get_snapshots,
                                   mount_task, prune_repo, remove_schedule,
                                   restore_snapshot, run_backup,
                                   schedule_backup, unmount_task)
from peerstash.core.db_schemas import TaskUpdate


# --- 1. Missing Task Validations ---
def test_missing_task_errors(mock_db, mocker):
    # Prevent the unmount safeguard from trying to execute real 'fusermount'
    mocker.patch("subprocess.run")
    funcs = [
        _verify_backup_size,
        _init_repo,
        run_backup,
        prune_repo,
        remove_schedule,
        restore_snapshot,
        get_snapshots,
        mount_task,
    ]
    for func in funcs:
        with pytest.raises(ValueError, match="not in DB"):
            func("non_existent_task")


# --- 2. schedule_backup String Parsing & Errors ---
def test_schedule_backup_invalid_name(mock_db, mocker):
    # Invalid Name
    mocker.patch("peerstash.core.backup.validate_task_name", return_value="Bad Name")
    with pytest.raises(ValueError, match="Bad Name"):
        schedule_backup("path", "peer")


def test_schedule_backup_types_and_daemon_error(mock_db, mocker, mock_daemon_and_locks):
    mocker.patch("peerstash.core.backup.db_host_exists", return_value=True)

    # Test passing single strings instead of lists
    name1 = schedule_backup("single_path", "peer", exclude_patterns="a|b")
    assert "/mnt/peerstash_root/single_path" in backup_mod.db_get_task(name1).include  # type: ignore
    assert backup_mod.db_get_task(name1).exclude == "a_b"  # type: ignore

    # Test passing a list for exclude
    name2 = schedule_backup("single_path", "peer", exclude_patterns=["x|y", "z"])
    assert backup_mod.db_get_task(name2).exclude == "x_y|z"  # type: ignore

    # Test Daemon Failure
    mocker.patch(
        "peerstash.core.backup.send_to_daemon", side_effect=RuntimeError("Daemon dead")
    )
    with pytest.raises(RuntimeError, match="Failed to create backup task"):
        schedule_backup("path", "peer")


# --- 3. Lock Exceptions ---
def test_lock_exceptions(mock_db, mocker, mock_restic):
    backup_mod.db_add_task("t", "/p", None, "h", "s", "1d", "p")
    backup_mod.db_update_task("t", TaskUpdate(status="idle"))  # Non-init state

    # Lock failures
    mocker.patch(
        "peerstash.core.backup.acquire_task_lock", side_effect=Exception("Lock Err")
    )
    with pytest.raises(RuntimeError, match="Lock Err"):
        run_backup("t")
    with pytest.raises(RuntimeError, match="Lock Err"):
        prune_repo("t")


# API exceptions
def test_api_exceptions(mock_db, mocker, mock_restic, mock_daemon_and_locks):
    backup_mod.db_add_task("t", "/p", None, "h", "s", "1d", "p")
    backup_mod.db_update_task("t", TaskUpdate(status="idle"))  # Non-init state

    # API failures
    mocker.patch("restic.forget", side_effect=Exception("Forget Err"))
    with pytest.raises(RuntimeError, match="Failed to prune"):
        prune_repo("t")

    mocker.patch("restic.snapshots", side_effect=Exception("API Err"))
    with pytest.raises(Exception, match="Failed to get snapshots"):
        get_snapshots("t")

    mocker.patch("subprocess.run")
    mocker.patch("subprocess.Popen", side_effect=Exception("Mount Err"))
    with pytest.raises(RuntimeError, match="Failed to mount repo"):
        mount_task("t")


# --- 4. Emergency Pruning & Space Check Logic ---
def test_verify_size_dry_run_fails(mock_db, mocker):
    backup_mod.db_add_task("t", "/p", None, "h", "s", "r", "p")
    backup_mod.db_update_task("t", TaskUpdate(status="idle"))  # Non-init state
    mocker.patch("peerstash.core.backup.get_disk_usage", return_value=(0, 0, 100))
    mocker.patch("peerstash.core.backup.run_backup", return_value=None)
    with pytest.raises(RuntimeError, match="Failed to get added bytes"):
        _verify_backup_size("t")


def test_run_backup_insufficient_space_triggers_prune(
    mock_db, mocker, mock_daemon_and_locks, mock_restic
):
    backup_mod.db_add_task("t", "/p", None, "h", "s", "r", "p")
    backup_mod.db_update_task("t", TaskUpdate(status="started"))  # Non-init state

    # Force free space < backup size
    mocker.patch("peerstash.core.backup._verify_backup_size", return_value=(10, 100))
    mock_prune = mocker.patch("peerstash.core.backup.prune_repo")

    with pytest.raises(RuntimeError, match="Not enough storage to complete task"):
        run_backup("t")

    mock_prune.assert_called_once_with("t", "1r", repack=False)


def test_run_backup_init_failure_fallback(mock_db, mocker, mock_daemon_and_locks):
    backup_mod.db_add_task("t", "/p", None, "h", "s", "r", "p")
    backup_mod.db_update_task("t", TaskUpdate(status="new"))

    mocker.patch("peerstash.core.backup._init_repo", side_effect=Exception("Init dead"))
    mock_sftp_rm = mocker.patch("peerstash.core.backup._sftp_recursive_remove")

    with pytest.raises(RuntimeError, match="Failed to initialize repo"):
        run_backup("t")
    mock_sftp_rm.assert_called_once()


def test_prune_strict_subprocess(mock_db, mocker, mock_daemon_and_locks, mock_restic):
    backup_mod.db_add_task("t", "/p", None, "h", "s", "1d", "p")
    backup_mod.db_update_task("t", TaskUpdate(status="idle"))

    mock_run = mocker.patch("subprocess.run")
    prune_repo("t", repack=False)
    assert "prune" in mock_run.call_args[0][0]

    mocker.patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "cmd"))
    with pytest.raises(RuntimeError, match="Failed to prune"):
        prune_repo("t", repack=False)


# --- 5. Paramiko SFTP Recursive Remove ---
def test_sftp_recursive_remove(mocker):
    mocker.patch("peerstash.core.backup.db_get_user", return_value="admin")
    mock_ssh = mocker.patch("paramiko.SSHClient")
    mock_sftp = mock_ssh.return_value.open_sftp.return_value

    # Simulate a file and a directory, then empty inside the nested directory
    mock_sftp.listdir.side_effect = [["file.txt", "dir"], []]

    # remove() succeeds on the file, but throws IOError on the dir, triggering recursion
    mock_sftp.remove.side_effect = [None, IOError(), None]

    _sftp_recursive_remove("host", "/path")

    assert mock_sftp.rmdir.call_count == 2
    assert mock_sftp.remove.call_count == 2


def test_sftp_recursive_remove_no_user(mocker):
    mocker.patch("peerstash.core.backup.db_get_user", return_value=None)
    with pytest.raises(ValueError, match="Unknown USER"):
        _sftp_recursive_remove("host", "/path")


# --- 6. File System Collisions & DB Errors ---
def test_restore_and_unmount_collisions(mock_db, mocker, mock_restic):
    backup_mod.db_add_task("t", "/p", None, "h", "s", "r", "p")
    backup_mod.db_update_task("t", TaskUpdate(last_run=datetime.now()))

    mocker.patch("os.path.exists", return_value=True)  # Force existing folders logic
    mock_rmtree = mocker.patch("shutil.rmtree")
    mocker.patch("shutil.move")
    mocker.patch("subprocess.run")  # Mock fusermount

    folder = restore_snapshot("t")
    assert folder is not None
    assert mock_rmtree.call_count > 0

    unmount_task("t")
    assert mock_rmtree.call_count > 1


def test_remove_schedule_db_failures(mock_db, mocker, mock_daemon_and_locks):
    backup_mod.db_add_task("t", "/p", None, "h", "s", "r", "p")

    mocker.patch(
        "peerstash.core.backup.send_to_daemon", side_effect=RuntimeError("dead")
    )
    with pytest.raises(RuntimeError, match="Failed to remove task"):
        remove_schedule("t")

    mocker.patch("peerstash.core.backup.send_to_daemon")
    mocker.patch("peerstash.core.backup.db_delete_task", return_value=False)
    with pytest.raises(RuntimeError, match="Failed to remove task .* database"):
        remove_schedule("t")
