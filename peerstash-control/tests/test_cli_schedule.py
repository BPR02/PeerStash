import pytest
from pytest_mock import MockerFixture, MockType
from typer.testing import CliRunner

from peerstash.cli.cmd_schedule import app


@pytest.fixture
def mock_schedule_deps(mocker: MockerFixture):
    """Provides standard mocks for the schedule command."""
    mock_schedule = mocker.patch(
        "peerstash.cli.cmd_schedule.schedule_backup", return_value="test_bkp"
    )
    mock_get_task = mocker.patch("peerstash.cli.cmd_schedule.db_get_task")
    return mock_schedule, mock_get_task


def test_schedule_new_task_success(
    runner: CliRunner, mock_schedule_deps: tuple[MockType, MockType]
):
    mock_schedule, mock_get_task = mock_schedule_deps
    mock_get_task.return_value = None  # Task does not exist yet

    result = runner.invoke(app, ["peer1", "--name", "test_bkp"])

    assert result.exit_code == 0
    assert "Creating new task test_bkp" in result.stdout
    assert "Backup task 'test_bkp' created" in result.stdout

    # Verify the core function got the default CLI arguments
    mock_schedule.assert_called_once_with(
        (["."]), "peer1", "4w3d", "0 3 * * *", "0 4 * * 0", None, "test_bkp"
    )


def test_schedule_existing_task_with_update_flag(
    runner: CliRunner, mock_schedule_deps: tuple[MockType, MockType]
):
    mock_schedule, mock_get_task = mock_schedule_deps
    mock_get_task.return_value = True  # Simulate task already exists

    result = runner.invoke(app, ["peer1", "--name", "test_bkp", "--update"])

    assert result.exit_code == 0
    assert "Updating task test_bkp" in result.stdout
    mock_schedule.assert_called_once()


def test_schedule_existing_task_interactive_confirm(
    runner: CliRunner, mock_schedule_deps: tuple[MockType, MockType]
):
    mock_schedule, mock_get_task = mock_schedule_deps
    mock_get_task.return_value = True

    # simulate the user typing 'y' and hitting Enter when prompted
    result = runner.invoke(app, ["peer1", "--name", "test_bkp"], input="y\n")

    assert result.exit_code == 0
    assert "already exists. Do you want to update it?" in result.stdout
    assert "Updating task test_bkp" in result.stdout
    mock_schedule.assert_called_once()


def test_schedule_existing_task_interactive_abort(
    runner: CliRunner, mock_schedule_deps: tuple[MockType, MockType]
):
    mock_schedule, mock_get_task = mock_schedule_deps
    mock_get_task.return_value = True

    # simulate the user typing 'n' and hitting Enter when prompted
    result = runner.invoke(app, ["peer1", "--name", "test_bkp"], input="n\n")

    assert result.exit_code == 1  # Abort triggers an exit 1
    assert "Aborted task update" in result.stderr
    mock_schedule.assert_not_called()


def test_schedule_value_error(
    runner: CliRunner, mock_schedule_deps: tuple[MockType, MockType]
):
    mock_schedule, mock_get_task = mock_schedule_deps
    mock_get_task.return_value = None
    mock_schedule.side_effect = ValueError("invalid cron")

    result = runner.invoke(app, ["peer1"])

    assert result.exit_code == 1
    assert "Error: invalid cron" in result.stderr


def test_schedule_system_error(
    runner: CliRunner, mock_schedule_deps: tuple[MockType, MockType]
):
    mock_schedule, mock_get_task = mock_schedule_deps
    mock_get_task.return_value = None
    mock_schedule.side_effect = Exception("db crash")

    result = runner.invoke(app, ["peer1"])

    assert result.exit_code == 1
    assert "System Error: db crash" in result.stderr
