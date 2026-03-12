import pytest
from pytest_mock import MockerFixture, MockType
from typer.testing import CliRunner

from peerstash.cli.cmd_list import app


@pytest.fixture
def mock_tasks(mocker: MockerFixture):
    """Provides standard task mocks for list formatting."""
    mock_task1 = mocker.MagicMock()
    mock_task1.name = "web_backup"
    mock_task1.status = "idle"
    mock_task1.hostname = "peerstash-alice"
    mock_task1.schedule = "0 3 * * *"
    mock_task1.include = "/mnt/peerstash_root/var/www"
    mock_task1.exclude = "*.log"
    mock_task1.prune_schedule = "0 4 * * 0"
    mock_task1.retention = "7d"
    mock_task1.last_run = "2026-03-01 12:00:00"
    mock_task1.last_exit_code = 0

    mock_task2 = mocker.MagicMock()
    mock_task2.name = "db_backup"
    mock_task2.status = "running"
    mock_task2.hostname = "peerstash-bob"

    # We only care about name and status for the minimal tests for task2

    return mocker.patch(
        "peerstash.cli.cmd_list.db_list_tasks", return_value=[mock_task1, mock_task2]
    )


def test_list_default(runner: CliRunner, mock_tasks):
    result = runner.invoke(app)

    assert result.exit_code == 0
    assert "web_backup" in result.stdout
    assert "db_backup" in result.stdout
    assert "idle" not in result.stdout  # Default mode shouldn't print status


def test_list_regex_filter(runner: CliRunner, mock_tasks):
    result = runner.invoke(app, ["web.*"])

    assert result.exit_code == 0
    assert "web_backup" in result.stdout
    assert "db_backup" not in result.stdout


def test_list_long_standard(runner: CliRunner, mock_tasks):
    result = runner.invoke(app, ["--long"])

    assert result.exit_code == 0
    # Checks the inline format and prefix stripping
    assert 'web_backup[idle] | alice "0 3 * * *" +[./var/www] -[*.log]' in result.stdout
    assert "2026-03-01" not in result.stdout  # Should omit last run without --all


def test_list_long_all(runner: CliRunner, mock_tasks):
    result = runner.invoke(app, ["--long", "--all"])

    assert result.exit_code == 0
    # Includes last run date and exit code
    assert "2026-03-01 12:00:00 (0)" in result.stdout


def test_list_long_human_readable(runner: CliRunner, mock_tasks):
    result = runner.invoke(app, ["--long", "--human_readable"])

    assert result.exit_code == 0
    # Checks multiline format
    assert "web_backup [idle]" in result.stdout
    assert "peer=       alice" in result.stdout
    assert "includes=   ./var/www" in result.stdout
    assert "last run=" not in result.stdout


def test_list_long_human_readable_all(runner: CliRunner, mock_tasks):
    result = runner.invoke(app, ["--long", "--human_readable", "--all"])

    assert result.exit_code == 0
    assert "last run=   2026-03-01 12:00:00 (0)" in result.stdout


def test_list_exception(runner: CliRunner, mocker: MockerFixture):
    mocker.patch(
        "peerstash.cli.cmd_list.db_list_tasks", side_effect=Exception("DB crash")
    )

    result = runner.invoke(app)

    assert result.exit_code == 1
    assert "System Error: DB crash" in result.stderr
