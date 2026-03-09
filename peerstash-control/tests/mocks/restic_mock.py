import os

import pytest
import restic
import restic.errors
from pytest_mock import MockerFixture


class MockCompletedProcess:
    """A dummy class to mimic subprocess.CompletedProcess."""

    def __init__(self, returncode: int, stderr: str):
        self.returncode = returncode
        self.stderr = stderr


def generate_restic_error(
    stderr_message: str, returncode: int = 1
) -> restic.errors.ResticFailedError:
    """Helper to generate the exact error raised by resticpy."""
    process = MockCompletedProcess(returncode, stderr_message)
    return restic.errors.ResticFailedError(
        f"Restic failed with exit code {process.returncode}: {process.stderr}"
    )


@pytest.fixture
def mock_restic(mocker: MockerFixture):
    """Mocks the resticpy commands used by the backup system."""

    # restic.init
    def mock_init(**kwargs):
        # Magic input to simulate a repository that already exists
        if kwargs.get("repo") == "sftp:user@host:/broken-path":
            raise generate_restic_error(
                "Fatal: create repository at sftp:user@host:/broken-path failed", 1
            )
        return "created restic repository a1b2c3d4"

    mocker.patch("restic.init", side_effect=mock_init)

    # restic.backup
    def mock_backup(paths=None, exclude_patterns=None, dry_run=False, **kwargs):
        # Simulate a storage full or permission error on a specific path
        if paths and "/forbidden_path" in paths:
            raise generate_restic_error(
                "Fatal: unable to save snapshot: storage full", 1
            )

        # Return a standard summary dictionary
        return {
            "files_new": 5,
            "files_changed": 2,
            "data_added": 1048576,
            "snapshot_id": "snap123",
        }

    mocker.patch("restic.backup", side_effect=mock_backup)

    # restic.check
    def mock_check(**kwargs):
        # Check both the explicitly passed repo and the environment variable
        repo = kwargs.get("repo", os.getenv("RESTIC_REPOSITORY", ""))

        # Magic input: If the repo path contains 'corrupted', simulate a failure
        if "corrupted" in repo:
            raise generate_restic_error(
                "Fatal: repository is corrupted: pack 8b3d2a does not exist", 1
            )

        return "no errors were found"

    mocker.patch("restic.check", side_effect=mock_check)

    # restic.forget
    def mock_forget(**kwargs):
        # Simulate a failure during the prune step
        if kwargs.get("prune") and kwargs.get("keep_last") == 0:
            raise generate_restic_error("Fatal: failed to prune repository", 1)
        return None  # forget/prune passes silently on success

    mocker.patch("restic.forget", side_effect=mock_forget)

    # restic.restore
    def mock_restore(snapshot_id, target_dir, **kwargs):
        # Simulate a missing temp_folder error
        if target_dir == "/nonexistent_temp":
            raise generate_restic_error(
                f"Fatal: target directory {target_dir} does not exist", 1
            )
        return None  # restore passes silently on success

    mocker.patch("restic.restore", side_effect=mock_restore)

    # restic.snapshots
    def mock_snapshots(snapshot_id=None, **kwargs):
        if snapshot_id == "invalid_id":
            raise generate_restic_error(f"Fatal: snapshot {snapshot_id} not found", 1)
        return [
            {"id": "snap123", "time": "2026-03-08T10:00:00.000Z", "paths": ["/data"]}
        ]

    mocker.patch("restic.snapshots", side_effect=mock_snapshots)
