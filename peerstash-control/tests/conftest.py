import pytest
from pathlib import Path
from pytest import MonkeyPatch
from pytest_mock import MockerFixture
from typer.testing import CliRunner


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


pytest_plugins = [
    "tests.mocks.tailscale_mock",
    "tests.mocks.sftpgo_mock",
    "tests.mocks.restic_mock",
    "tests.mocks.subprocess_mock",
    "tests.mocks.db_mock",
]


@pytest.fixture(autouse=True)
def mock_setup(mocker: MockerFixture) -> None:
    # don't check for cli setup before running cli commands
    mocker.patch("peerstash.cli.utils.check_setup", return_value=True)
