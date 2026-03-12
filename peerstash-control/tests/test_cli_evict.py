import pytest
from pytest_mock import MockerFixture, MockType
from typer.testing import CliRunner

from peerstash.cli.cmd_evict import app


@pytest.fixture
def mock_evict_deps(mocker: MockerFixture):
    mock_exists = mocker.patch(
        "peerstash.cli.cmd_evict.db_host_exists", return_value=True
    )
    mock_delete = mocker.patch("peerstash.cli.cmd_evict.registration.delete_peer")
    mock_get_tasks = mocker.patch(
        "peerstash.cli.cmd_evict.db_get_tasks_for_host", return_value=["task1", "task2"]
    )
    mock_remove = mocker.patch("peerstash.cli.cmd_evict.remove_schedule")
    return mock_exists, mock_delete, mock_get_tasks, mock_remove


def test_evict_force_flag_success(
    runner: CliRunner, mock_evict_deps: tuple[MockType, MockType, MockType, MockType]
):
    mock_exists, mock_delete, mock_get_tasks, mock_remove = mock_evict_deps

    result = runner.invoke(app, ["bob", "--force"])

    assert result.exit_code == 0
    assert "Removed from 'bob' peers list" in result.stdout
    mock_delete.assert_called_once_with("bob")
    # Assert remove_schedule was called for both task1 and task2
    assert mock_remove.call_count == 2


def test_evict_interactive_confirm(
    runner: CliRunner, mock_evict_deps: tuple[MockType, MockType, MockType, MockType]
):
    mock_exists, mock_delete, mock_get_tasks, mock_remove = mock_evict_deps

    result = runner.invoke(app, ["bob"], input="y\n")

    assert result.exit_code == 0
    mock_delete.assert_called_once_with("bob")


def test_evict_interactive_abort(
    runner: CliRunner, mock_evict_deps: tuple[MockType, MockType, MockType, MockType]
):
    mock_exists, mock_delete, mock_get_tasks, mock_remove = mock_evict_deps

    result = runner.invoke(app, ["bob"], input="n\n")

    assert result.exit_code == 1
    assert "Aborted peer eviction" in result.stderr
    mock_delete.assert_not_called()


def test_evict_unknown_peer(
    runner: CliRunner, mock_evict_deps: tuple[MockType, MockType, MockType, MockType]
):
    mock_exists, mock_delete, mock_get_tasks, mock_remove = mock_evict_deps
    mock_exists.return_value = False

    result = runner.invoke(app, ["unknown"])

    assert result.exit_code == 1
    assert "Unknown peer" in result.stderr
