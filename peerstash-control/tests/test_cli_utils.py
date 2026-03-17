import pytest
import typer
from pytest import CaptureFixture
from pytest_mock import MockerFixture

from peerstash.cli.utils import check_setup


def test_check_setup_success(mocker: MockerFixture):
    # Setup is complete if an invite code exists
    mocker.patch("peerstash.cli.utils.db_get_invite_code", return_value="abc123xyz")

    # Should run silently without raising an error
    check_setup()


def test_check_setup_failure(mocker: MockerFixture, capsys: CaptureFixture):
    # Setup is incomplete if there is no invite code
    mocker.patch("peerstash.cli.utils.db_get_invite_code", return_value=None)

    with pytest.raises(typer.Exit) as exc_info:
        check_setup()

    assert exc_info.value.exit_code == 1

    captured = capsys.readouterr()
    assert "Not initialized" in captured.err
    assert "Have you run 'peerstash setup'?" in captured.err
