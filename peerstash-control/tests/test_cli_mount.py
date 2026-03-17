import pytest
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from peerstash.cli.cmd_mount import app


def test_cancel_success(mock_setup, runner: CliRunner, mocker: MockerFixture):
    mock_run = mocker.patch("peerstash.cli.cmd_mount.mount_task")

    result = runner.invoke(app, ["my_task"])

    assert result.exit_code == 0
    assert "mounted" in result.stdout
    mock_run.assert_called_once_with("my_task")


def test_cancel_value_error(runner: CliRunner, mocker: MockerFixture):
    mocker.patch(
        "peerstash.cli.cmd_mount.mount_task",
        side_effect=ValueError("Task not found"),
    )

    result = runner.invoke(app, ["bad_task"])

    assert result.exit_code == 1
    assert "Error: Task not found" in result.stderr


def test_cancel_system_error(runner: CliRunner, mocker: MockerFixture):
    mocker.patch(
        "peerstash.cli.cmd_mount.mount_task", side_effect=Exception("Daemon down")
    )

    result = runner.invoke(app, ["my_task"])

    assert result.exit_code == 1
    assert "System Error: Daemon down" in result.stderr
