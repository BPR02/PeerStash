import pytest
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from peerstash.cli.cmd_peers import app


def test_peers_success(runner: CliRunner, mocker: MockerFixture):
    mock_host = mocker.MagicMock()
    mock_host.hostname = "peerstash-alice"

    mocker.patch("peerstash.cli.cmd_peers.db_list_hosts", return_value=[mock_host])
    mocker.patch("peerstash.cli.cmd_peers.db_get_user", return_value="admin")

    # Fake the disk usage so we don't invoke SSH
    mocker.patch(
        "peerstash.cli.cmd_peers.get_disk_usage", return_value=(2048, 1024, 1024)
    )

    result = runner.invoke(app)

    assert result.exit_code == 0
    assert "alice (1.0KiB used / 2.0KiB)" in result.stdout


def test_peers_no_user(runner: CliRunner, mocker: MockerFixture):
    mocker.patch("peerstash.cli.cmd_peers.db_list_hosts", return_value=[])
    mocker.patch("peerstash.cli.cmd_peers.db_get_user", return_value=None)

    result = runner.invoke(app)

    assert result.exit_code == 1
    assert "Error: unknown user" in result.stderr


def test_peers_db_error(runner: CliRunner, mocker: MockerFixture):
    mocker.patch(
        "peerstash.cli.cmd_peers.db_list_hosts",
        side_effect=Exception("Database locked"),
    )

    result = runner.invoke(app)

    assert result.exit_code == 1
    assert "Error: Database locked" in result.stderr
