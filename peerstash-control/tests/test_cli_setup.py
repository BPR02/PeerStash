import pytest
import typer
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from peerstash.cli.cmd_setup import app


@pytest.fixture
def mock_setup_deps(mocker: MockerFixture) -> MockerFixture:
    """Mocks all dependencies except the interactive prompts."""
    mocker.patch("peerstash.cli.cmd_setup.db_get_invite_code", return_value=None)
    mocker.patch("peerstash.cli.cmd_setup.db_get_user", return_value="admin")
    mocker.patch("peerstash.cli.cmd_setup.db_set_invite_code")
    mocker.patch("peerstash.cli.cmd_setup.verify_sudo_password")
    mocker.patch("peerstash.cli.cmd_setup.gen_restic_pass")

    # Mock tailscale system calls
    mocker.patch("peerstash.cli.cmd_setup.tailscale.modify_policy")
    mocker.patch("peerstash.cli.cmd_setup.tailscale.register_device")
    mocker.patch(
        "peerstash.cli.cmd_setup.tailscale.generate_device_invite",
        return_value="invite_abc123",
    )
    mocker.patch(
        "peerstash.cli.cmd_setup.tailscale.revoke_api_token", return_value=True
    )

    # Base mock for _get_sudo_password so it doesn't consume sys.stdin in every test
    mocker.patch(
        "peerstash.cli.cmd_setup._get_sudo_password", return_value="dummy_pass"
    )

    return mocker


def test_setup_interactive_prompts_success(
    runner: CliRunner, mock_setup_deps: MockerFixture
):
    mocker = mock_setup_deps

    # We explicitly test the interactive prompt path by simulating the Typer prompt
    def mock_interactive_sudo():
        return typer.prompt("[peerstash] enter password for admin", hide_input=True)

    mocker.patch(
        "peerstash.cli.cmd_setup._get_sudo_password", side_effect=mock_interactive_sudo
    )

    # 1st line: sudo pass, 2nd line: API token
    result = runner.invoke(app, input="my_sudo_pass\ntskey-api-12345\n")

    assert result.exit_code == 0
    assert "enter password for admin" in result.stdout
    assert "Paste API Access Token" in result.stdout
    assert "Success" in result.stdout


def test_setup_piped_stdin_success(runner: CliRunner, mock_setup_deps: MockerFixture):
    mocker = mock_setup_deps
    mock_verify = mocker.patch("peerstash.cli.cmd_setup.verify_sudo_password")

    # Simulate the exact logic of the real _get_sudo_password under piped conditions
    def mock_piped_sudo():
        import sys

        return sys.stdin.read().strip()

    mocker.patch(
        "peerstash.cli.cmd_setup._get_sudo_password", side_effect=mock_piped_sudo
    )

    # Pass token via CLI arg, so it ONLY prompts for sudo password via stdin
    result = runner.invoke(
        app, ["--token", "tskey-api-12345"], input="piped_sudo_pass\n"
    )

    assert result.exit_code == 0
    mock_verify.assert_called_once_with("piped_sudo_pass")
    assert "Success" in result.stdout


def test_setup_already_configured(runner: CliRunner, mock_setup_deps: MockerFixture):
    mocker = mock_setup_deps
    mocker.patch(
        "peerstash.cli.cmd_setup.db_get_invite_code", return_value="already_set"
    )

    result = runner.invoke(app)

    assert result.exit_code == 0
    assert "already configured" in result.stdout


def test_setup_overwrite_flag(runner: CliRunner, mock_setup_deps: MockerFixture):
    mocker = mock_setup_deps
    mocker.patch("sys.stdin.isatty", return_value=True)
    mocker.patch(
        "peerstash.cli.cmd_setup.db_get_invite_code", return_value="already_set"
    )

    # The --overwrite flag should bypass the "already configured" check
    result = runner.invoke(app, ["--overwrite"], input="tskey-api-12345\n")

    assert result.exit_code == 0
    assert "Success" in result.stdout
    assert "already configured" not in result.stdout


def test_setup_sudo_verification_failure(
    runner: CliRunner, mock_setup_deps: MockerFixture
):
    mocker = mock_setup_deps
    mocker.patch("sys.stdin.isatty", return_value=True)
    mocker.patch(
        "peerstash.cli.cmd_setup.verify_sudo_password",
        side_effect=ValueError("Incorrect password"),
    )

    result = runner.invoke(app, ["--token", "tskey"], input="wrong_pass\n")

    assert result.exit_code == 1
    assert "Error: Incorrect password" in result.stderr


def test_setup_missing_user(runner: CliRunner, mock_setup_deps: MockerFixture):
    mocker = mock_setup_deps
    mocker.patch("sys.stdin.isatty", return_value=True)
    # Simulate a corrupted DB where no user is returned
    mocker.patch("peerstash.cli.cmd_setup.db_get_user", return_value=None)

    result = runner.invoke(app, ["--token", "tskey"], input="pass\n")

    assert result.exit_code == 1
    assert "User not set. Database may be corrupted." in result.stderr


def test_setup_token_revoke_failure_warning(
    runner: CliRunner, mock_setup_deps: MockerFixture
):
    mocker = mock_setup_deps
    mocker.patch("sys.stdin.isatty", return_value=True)
    # Simulate tailscale failing to revoke the token, returning False
    mocker.patch(
        "peerstash.cli.cmd_setup.tailscale.revoke_api_token", return_value=False
    )

    result = runner.invoke(app, ["--token", "tskey"], input="pass\n")

    assert result.exit_code == 0
    assert "API Token could not be automatically revoked" in result.stdout
    assert "Success" in result.stdout
