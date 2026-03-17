import pytest
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from peerstash.cli.cmd_id import app


def test_id_success(runner: CliRunner, mocker: MockerFixture):
    mock_gen = mocker.patch(
        "peerstash.cli.cmd_id.identity.generate_share_key",
        return_value="peerstash.alice#abcd123",
    )

    result = runner.invoke(app)

    assert result.exit_code == 0
    assert "peerstash.alice#abcd123" in result.stdout
    mock_gen.assert_called_once()


def test_id_value_error(runner: CliRunner, mocker: MockerFixture):
    mocker.patch(
        "peerstash.cli.cmd_id.identity.generate_share_key",
        side_effect=ValueError("Keys not found"),
    )

    result = runner.invoke(app)

    assert result.exit_code == 1
    assert "Error: Keys not found" in result.stderr
