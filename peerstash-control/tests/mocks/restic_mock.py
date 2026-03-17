import os

import pytest
import restic.errors
from pytest_mock import MockerFixture


def generate_restic_error(msg: str, exit_code: int = 1):
    return restic.errors.ResticFailedError(
        f"Restic failed with exit code {exit_code}: {msg}"
    )


@pytest.fixture
def mock_restic(mocker: MockerFixture):
    """Mocks the resticpy commands used by the backup system."""

    # restic.init
    def mock_init(*args, **kwargs):
        if "corrupted" in os.getenv("RESTIC_REPOSITORY", ""):
            raise generate_restic_error("Fatal: repository corrupted", 1)

    mocker.patch("restic.init", side_effect=mock_init)

    # restic.backup
    def mock_backup(paths=None, exclude_patterns=None, dry_run=False, **kwargs):
        # Only trigger the failure on the REAL backup, not the dry run
        if os.getenv("MOCK_BACKUP_FAIL") == "1" and not dry_run:
            raise generate_restic_error("Fatal: Permission denied", 1)

        # Return a standard summary dictionary
        return {
            "files_new": 5,
            "files_changed": 2,
            "data_added": 1048576,
            "snapshot_id": "snap123",
        }

    mocker.patch("restic.backup", side_effect=mock_backup)

    # restic.check
    def mock_check(*args, **kwargs):
        if "corrupted" in os.getenv("RESTIC_REPOSITORY", ""):
            return False
        return True

    mocker.patch("restic.check", side_effect=mock_check)

    # restic.forget
    def mock_forget(**kwargs):
        # Simulate a failure during the prune step
        if kwargs.get("prune") and kwargs.get("keep_last") == 0:
            raise generate_restic_error("Fatal: failed to prune repository", 1)
        return None  # forget/prune passes silently on success

    mocker.patch("restic.forget", side_effect=mock_forget)

    # restic.restore
    def mock_restore(*args, **kwargs):
        if os.getenv("MOCK_RESTORE_FAIL") == "1":
            raise generate_restic_error("Fatal: target directory does not exist", 1)

    mocker.patch("restic.restore", side_effect=mock_restore)

    # restic.snapshots
    def mock_snapshots(*args, **kwargs):
        return [{"id": "snap123", "time": "2026-03-01T12:00:00Z"}]

    mocker.patch("restic.snapshots", side_effect=mock_snapshots)

    # restic.unlock
    mocker.patch("restic.unlock")
