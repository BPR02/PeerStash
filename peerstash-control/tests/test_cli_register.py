import pytest
from pytest_mock import MockerFixture, MockType
from typer.testing import CliRunner

from peerstash.cli.cmd_register import app


@pytest.fixture
def mock_reg_deps(mocker: MockerFixture):
    """Provides standard mocks for the register command."""
    mock_parse = mocker.patch(
        "peerstash.cli.cmd_register.registration.parse_share_key",
        return_value={"username": "bob", "invite_code": "abcXYZ"},
    )
    mock_exists = mocker.patch(
        "peerstash.cli.cmd_register.db_host_exists", return_value=False
    )
    mock_upsert = mocker.patch("peerstash.cli.cmd_register.registration.upsert_peer")
    return mock_parse, mock_exists, mock_upsert


def test_register_new_user_success(
    runner: CliRunner, mock_reg_deps: tuple[MockType, MockType, MockType]
):
    mock_parse, mock_exists, mock_upsert = mock_reg_deps

    result = runner.invoke(app, ["peerstash.bob#fake_base64_payload", "20"])

    assert result.exit_code == 0
    assert "Creating new user bob" in result.stdout
    assert "Success! User bob created with quota of 20 GiB" in result.stdout
    assert "https://login.tailscale.com/admin/invite/abcXYZ" in result.stdout

    mock_parse.assert_called_once_with("peerstash.bob#fake_base64_payload")
    mock_upsert.assert_called_once_with(
        {"username": "bob", "invite_code": "abcXYZ"}, 20, allow_update=False
    )


def test_register_new_user_default_quota(
    runner: CliRunner,
    mock_reg_deps: tuple[MockType, MockType, MockType],
    mocker: MockerFixture,
):
    mock_parse, mock_exists, mock_upsert = mock_reg_deps

    # Missing quota argument, should default to 10
    result = runner.invoke(app, ["peerstash.bob#fake_base64_payload"])

    assert result.exit_code == 0
    mock_upsert.assert_called_once_with(mocker.ANY, 10, allow_update=False)


def test_register_existing_user_yes_flag(
    runner: CliRunner,
    mock_reg_deps: tuple[MockType, MockType, MockType],
    mocker: MockerFixture,
):
    mock_parse, mock_exists, mock_upsert = mock_reg_deps
    mock_exists.return_value = True

    result = runner.invoke(app, ["peerstash.bob#payload", "15", "--yes"])

    assert result.exit_code == 0
    assert "Updating user bob" in result.stdout
    mock_upsert.assert_called_once_with(mocker.ANY, 15, allow_update=True)


def test_register_existing_user_interactive_confirm(
    runner: CliRunner, mock_reg_deps: tuple[MockType, MockType, MockType]
):
    mock_parse, mock_exists, mock_upsert = mock_reg_deps
    mock_exists.return_value = True

    result = runner.invoke(app, ["peerstash.bob#payload", "15"], input="y\n")

    assert result.exit_code == 0
    assert "already exists" in result.stdout
    assert "Updating user bob" in result.stdout
    mock_upsert.assert_called_once()


def test_register_existing_user_interactive_abort(
    runner: CliRunner, mock_reg_deps: tuple[MockType, MockType, MockType]
):
    mock_parse, mock_exists, mock_upsert = mock_reg_deps
    mock_exists.return_value = True

    result = runner.invoke(app, ["peerstash.bob#payload", "15"], input="n\n")

    assert result.exit_code == 1
    assert "Aborted user update" in result.stderr
    mock_upsert.assert_not_called()


def test_register_runtime_error(
    runner: CliRunner, mock_reg_deps: tuple[MockType, MockType, MockType]
):
    mock_parse, mock_exists, mock_upsert = mock_reg_deps
    mock_upsert.side_effect = RuntimeError("SFTPGo connection failed")

    result = runner.invoke(app, ["peerstash.bob#payload"])

    assert result.exit_code == 1
    assert "Error: SFTPGo connection failed" in result.stderr


def test_evict_value_error(runner: CliRunner, mocker: MockerFixture):
    mocker.patch(
        "peerstash.cli.cmd_register.registration.parse_share_key",
        side_effect=ValueError("Invalid share key"),
    )

    result = runner.invoke(app, ["peerstash.bob#payload"])

    assert result.exit_code == 1
    assert "Error: Invalid share key" in result.stderr


def test_evict_system_error(runner: CliRunner, mocker: MockerFixture):
    mocker.patch(
        "peerstash.cli.cmd_register.registration.parse_share_key",
        side_effect=Exception("Daemon down"),
    )

    result = runner.invoke(app, ["peerstash.bob#payload"])

    assert result.exit_code == 1
    assert "System Error: Daemon down" in result.stderr
