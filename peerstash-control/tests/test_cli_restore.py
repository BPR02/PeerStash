import pytest
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from peerstash.cli.cmd_restore import app


def test_restore_success_defaults(runner: CliRunner, mocker: MockerFixture):
    mock_restore = mocker.patch(
        "peerstash.cli.cmd_restore.restore_snapshot", return_value="my_task_latest"
    )

    result = runner.invoke(app, ["my_task"])

    assert result.exit_code == 0
    assert "Task 'my_task' restored. Files in my_task_latest" in result.stdout
    # Should use the default 'latest' snapshot and None for include/exclude
    mock_restore.assert_called_once_with("my_task", "latest", None, None)


def test_restore_success_with_args_and_lists(runner: CliRunner, mocker: MockerFixture):
    mock_restore = mocker.patch(
        "peerstash.cli.cmd_restore.restore_snapshot", return_value="my_task_snap123"
    )

    # Simulating multiple --exclude flags
    result = runner.invoke(
        app,
        [
            "my_task",
            "snap123",
            "--include",
            ".*txt",
            "--exclude",
            ".*mp4",
            "--exclude",
            ".*mkv",
        ],
    )

    assert result.exit_code == 0
    mock_restore.assert_called_once_with(
        "my_task", "snap123", ".*txt", [".*mp4", ".*mkv"]
    )


def test_restore_value_error(runner: CliRunner, mocker: MockerFixture):
    mocker.patch(
        "peerstash.cli.cmd_restore.restore_snapshot",
        side_effect=ValueError("Task not in DB"),
    )

    result = runner.invoke(app, ["bad_task"])

    assert result.exit_code == 1
    assert "Error: Task not in DB" in result.stderr


def test_restore_runtime_error(runner: CliRunner, mocker: MockerFixture):
    mocker.patch(
        "peerstash.cli.cmd_restore.restore_snapshot",
        side_effect=RuntimeError("Could not remove folder"),
    )

    result = runner.invoke(app, ["bad_task"])

    assert result.exit_code == 1
    assert "Error: Could not remove folder" in result.stderr


def test_restore_system_error(runner: CliRunner, mocker: MockerFixture):
    mocker.patch(
        "peerstash.cli.cmd_restore.restore_snapshot", side_effect=Exception("Disk full")
    )

    result = runner.invoke(app, ["my_task"])

    assert result.exit_code == 1
    assert "System Error: Disk full" in result.stderr
