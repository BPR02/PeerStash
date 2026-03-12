import pytest
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from peerstash.cli.cmd_prune import app


def test_prune_success(runner: CliRunner, mocker: MockerFixture):
    mock_prune = mocker.patch("peerstash.cli.cmd_prune.prune_repo")

    result = runner.invoke(app, ["my_task"])

    assert result.exit_code == 0
    assert "Repository for task 'my_task' has been pruned." in result.stdout
    mock_prune.assert_called_once_with("my_task", offset=0)


def test_prune_with_offset(runner: CliRunner, mocker: MockerFixture):
    mock_prune = mocker.patch("peerstash.cli.cmd_prune.prune_repo")

    result = runner.invoke(app, ["my_task", "45"])

    assert result.exit_code == 0
    mock_prune.assert_called_once_with("my_task", offset=45)


def test_prune_value_error(runner: CliRunner, mocker: MockerFixture):
    mocker.patch(
        "peerstash.cli.cmd_prune.prune_repo",
        side_effect=ValueError("Task with name 'my_task' not in DB"),
    )

    result = runner.invoke(app, ["my_task"])

    assert result.exit_code == 1
    assert "Error: Task with name 'my_task' not in DB" in result.stderr


def test_prune_system_error(runner: CliRunner, mocker: MockerFixture):
    mocker.patch(
        "peerstash.cli.cmd_prune.prune_repo",
        side_effect=Exception("Failed to lock repository"),
    )

    result = runner.invoke(app, ["my_task"])

    assert result.exit_code == 1
    assert "System Error: Failed to lock repository" in result.stderr
