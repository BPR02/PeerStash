import pytest
from unittest.mock import MagicMock
from pytest_mock import MockerFixture, MockType
from typer.testing import CliRunner

from peerstash.cli.cmd_snapshots import app


@pytest.fixture
def mock_snap_deps(mocker: MockerFixture) -> tuple[MockType, MockType, MagicMock]:
    """Provides standard dependencies for snapshots."""
    mock_task = mocker.MagicMock()
    mock_task.name = "web_backup"
    mock_task.status = "idle"

    mock_get_task = mocker.patch(
        "peerstash.cli.cmd_snapshots.db_get_task", return_value=mock_task
    )

    snaps = [
        {
            "id": "1234567890abcdef",
            "short_id": "12345678",
            "time": "2026-03-01T12:00:00Z",
            "paths": ["/mnt/peerstash_root/var/www"],
        }
    ]
    mock_get_snapshots = mocker.patch(
        "peerstash.cli.cmd_snapshots.get_snapshots", return_value=snaps
    )

    return mock_get_task, mock_get_snapshots, mock_task


def test_snapshots_success_default(
    runner: CliRunner, mock_snap_deps: tuple[MockType, MockType, MagicMock]
):
    result = runner.invoke(app, ["web_backup"])

    assert result.exit_code == 0
    assert "1234567890abcdef" in result.stdout
    assert "Short ID: 12345678" in result.stdout
    assert "Date:" in result.stdout
    assert "- ./var/www" in result.stdout  # Verifying the path replacement logic works


def test_snapshots_success_json(
    runner: CliRunner, mock_snap_deps: tuple[MockType, MockType, MagicMock]
):
    result = runner.invoke(app, ["web_backup", "--json"])

    assert result.exit_code == 0
    # Because it prints a raw Python dict via list format, we check the exact string representation
    assert "'short_id': '12345678'" in result.stdout
    assert "'id': '1234567890abcdef'" in result.stdout
    assert "Short ID:" not in result.stdout  # Standard formatter should be bypassed


def test_snapshots_missing_task(
    runner: CliRunner, mock_snap_deps: tuple[MockType, MockType, MagicMock]
):
    mock_get_task, _, _ = mock_snap_deps
    mock_get_task.return_value = None

    result = runner.invoke(app, ["bad_task"])

    assert result.exit_code == 1
    assert "Task 'bad_task' does not exist" in result.stderr


def test_snapshots_new_task(
    runner: CliRunner, mock_snap_deps: tuple[MockType, MockType, MagicMock]
):
    _, _, mock_task = mock_snap_deps
    mock_task.status = "new"  # Trigger the safeguard

    result = runner.invoke(app, ["web_backup"])

    assert result.exit_code == 1
    assert "has not been backed up yet" in result.stderr


def test_snapshots_restic_error(
    runner: CliRunner, mock_snap_deps: tuple[MockType, MockType, MagicMock]
):
    _, mock_get_snapshots, _ = mock_snap_deps
    mock_get_snapshots.side_effect = Exception("Restic repo corrupted")

    result = runner.invoke(app, ["web_backup"])

    assert result.exit_code == 1
    assert "Error: Restic repo corrupted" in result.stderr
