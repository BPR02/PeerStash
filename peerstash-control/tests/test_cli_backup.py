import pytest
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from peerstash.cli.cmd_backup import app


def test_backup_success(mock_setup, runner: CliRunner, mocker: MockerFixture):
    mock_run = mocker.patch("peerstash.cli.cmd_backup.run_backup")

    result = runner.invoke(app, ["my_task"])

    assert result.exit_code == 0
    assert "completed" in result.stdout
    mock_run.assert_called_once_with("my_task", offset=0)


def test_backup_with_offset(runner: CliRunner, mocker: MockerFixture):
    mock_run = mocker.patch("peerstash.cli.cmd_backup.run_backup")

    result = runner.invoke(app, ["my_task", "15"])

    assert result.exit_code == 0
    mock_run.assert_called_once_with("my_task", offset=15)


def test_backup_value_error(runner: CliRunner, mocker: MockerFixture):
    mocker.patch(
        "peerstash.cli.cmd_backup.run_backup", side_effect=ValueError("Task not found")
    )

    result = runner.invoke(app, ["bad_task"])

    assert result.exit_code == 1
    assert "Error: Task not found" in result.stderr


def test_backup_system_error(runner: CliRunner, mocker: MockerFixture):
    mocker.patch(
        "peerstash.cli.cmd_backup.run_backup", side_effect=Exception("Daemon down")
    )

    result = runner.invoke(app, ["my_task"])

    assert result.exit_code == 1
    assert "System Error: Daemon down" in result.stderr
